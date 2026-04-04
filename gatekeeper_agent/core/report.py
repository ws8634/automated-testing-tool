"""
报告生成模块
支持多种格式：Markdown、JSON、HTML
"""

import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path

from jinja2 import Template

from gatekeeper_agent.models.scan import ScanResult, Violation
from gatekeeper_agent.utils.logger import get_logger

logger = get_logger(__name__)


class ReportGenerator:
    """报告生成器"""
    
    # Markdown 报告模板
    MARKDOWN_TEMPLATE = """# Gatekeeper 代码审核报告

## 扫描概览

| 项目 | 值 |
|------|-----|
| 扫描ID | {{ result.scan_id }} |
| 扫描时间 | {{ result.start_time.strftime('%Y-%m-%d %H:%M:%S') }} |
| 代码来源 | {{ result.source_type.value }} |
| 扫描文件数 | {{ result.summary.total_files }} |
| 扫描代码行数 | {{ result.summary.total_lines }} |

## 风险统计

| 风险等级 | 数量 | 状态 |
|----------|------|------|
| 🔴 Fatal | {{ result.summary.fatal_count }} | {% if result.summary.fatal_count > 0 %}❌ 需立即处理{% else %}✅ 通过{% endif %} |
| 🟠 Error | {{ result.summary.error_count }} | {% if result.summary.error_count > 0 %}⚠️ 需审批{% else %}✅ 通过{% endif %} |
| 🟡 Warning | {{ result.summary.warning_count }} | {% if result.summary.warning_count > 0 %}💡 建议优化{% else %}✅ 通过{% endif %} |
| 🔵 Info | {{ result.summary.info_count }} | 信息 |

**总计: {{ result.summary.total_violations }} 个问题**

{% if result.has_blocking_violations() %}
⚠️ **警告: 发现阻断性违规，请修复后再提交代码！**
{% endif %}

---

## 详细违规列表

{% if result.violations %}
{% for violation in result.violations %}
### {{ loop.index }}. {{ violation.rule_name }}

**规则ID:** `{{ violation.rule_id }}`  
**风险等级:** {{ violation.severity }}  
**分类:** {{ violation.category }}  
**文件:** `{{ violation.file_path or "N/A" }}`  
**位置:** 第 {{ violation.location.line_number }} 行，第 {{ violation.location.column_start }}-{{ violation.location.column_end }} 列

**问题描述:**
{{ violation.message }}

**违规代码:**
```
{{ violation.location.matched_text }}
```

{% if violation.suggested_fix %}
**修复建议:**
```
{{ violation.suggested_fix }}
```
{% endif %}

{% if violation.cascade_results %}
**级联检查结果:**
{% for cascade in violation.cascade_results %}
- {{ cascade.check_name }}: {% if cascade.passed %}✅ 通过{% else %}❌ 失败{% endif %} - {{ cascade.message }}
{% endfor %}
{% endif %}

{% if violation.docs_link %}
📚 [查看文档]({{ violation.docs_link }})
{% endif %}

---

{% endfor %}
{% else %}
✅ 未发现违规项，代码审核通过！
{% endif %}

---

*报告生成时间: {{ now }}*
*由 Gatekeeper Agent 自动生成*
"""

    # HTML 报告模板
    HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gatekeeper 代码审核报告</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .summary-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 30px; }
        .card { 
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card h3 { font-size: 14px; color: #666; margin-bottom: 8px; }
        .card .value { font-size: 32px; font-weight: bold; }
        .severity-fatal { color: #dc3545; }
        .severity-error { color: #fd7e14; }
        .severity-warning { color: #ffc107; }
        .severity-info { color: #17a2b8; }
        .violations-list { background: white; border-radius: 8px; padding: 20px; }
        .violation-item { 
            border-left: 4px solid #ddd;
            padding: 15px;
            margin-bottom: 15px;
            background: #f8f9fa;
            border-radius: 4px;
        }
        .violation-item.fatal { border-left-color: #dc3545; }
        .violation-item.error { border-left-color: #fd7e14; }
        .violation-item.warning { border-left-color: #ffc107; }
        .violation-item.info { border-left-color: #17a2b8; }
        .violation-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
        .violation-title { font-size: 18px; font-weight: bold; }
        .badge { 
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            color: white;
        }
        .badge-fatal { background: #dc3545; }
        .badge-error { background: #fd7e14; }
        .badge-warning { background: #ffc107; color: #333; }
        .badge-info { background: #17a2b8; }
        .code-block { 
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 4px;
            overflow-x: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 14px;
            margin: 10px 0;
        }
        .meta-info { color: #666; font-size: 14px; margin: 5px 0; }
        .alert { 
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 20px;
        }
        .alert-danger { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .footer { text-align: center; color: #666; margin-top: 30px; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Gatekeeper 代码审核报告</h1>
            <p>扫描ID: {{ result.scan_id }} | 时间: {{ result.start_time.strftime('%Y-%m-%d %H:%M:%S') }}</p>
        </div>
        
        <div class="summary-cards">
            <div class="card">
                <h3>扫描文件</h3>
                <div class="value">{{ result.summary.total_files }}</div>
            </div>
            <div class="card">
                <h3>代码行数</h3>
                <div class="value">{{ result.summary.total_lines }}</div>
            </div>
            <div class="card">
                <h3>Fatal</h3>
                <div class="value severity-fatal">{{ result.summary.fatal_count }}</div>
            </div>
            <div class="card">
                <h3>Error</h3>
                <div class="value severity-error">{{ result.summary.error_count }}</div>
            </div>
            <div class="card">
                <h3>Warning</h3>
                <div class="value severity-warning">{{ result.summary.warning_count }}</div>
            </div>
        </div>
        
        {% if result.has_blocking_violations() %}
        <div class="alert alert-danger">
            ⚠️ <strong>警告:</strong> 发现阻断性违规，请修复后再提交代码！
        </div>
        {% else %}
        <div class="alert alert-success">
            ✅ <strong>通过:</strong> 未发现阻断性违规！
        </div>
        {% endif %}
        
        <div class="violations-list">
            <h2>详细违规列表</h2>
            {% if result.violations %}
                {% for violation in result.violations %}
                <div class="violation-item {{ violation.severity }}">
                    <div class="violation-header">
                        <span class="violation-title">{{ violation.rule_name }}</span>
                        <span class="badge badge-{{ violation.severity }}">{{ violation.severity.upper() }}</span>
                    </div>
                    <div class="meta-info">
                        <strong>规则ID:</strong> {{ violation.rule_id }} | 
                        <strong>分类:</strong> {{ violation.category }} | 
                        <strong>文件:</strong> {{ violation.file_path or "N/A" }} | 
                        <strong>位置:</strong> 第 {{ violation.location.line_number }} 行
                    </div>
                    <p style="margin: 10px 0;">{{ violation.message }}</p>
                    <div class="code-block">{{ violation.matched_content }}</div>
                    {% if violation.suggested_fix %}
                    <div style="margin-top: 10px;">
                        <strong>修复建议:</strong>
                        <div class="code-block">{{ violation.suggested_fix }}</div>
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            {% else %}
                <p style="text-align: center; padding: 40px; color: #28a745;">
                    ✅ 未发现违规项，代码审核通过！
                </p>
            {% endif %}
        </div>
        
        <div class="footer">
            <p>报告生成时间: {{ now }} | 由 Gatekeeper Agent 自动生成</p>
        </div>
    </div>
</body>
</html>
"""

    def __init__(self):
        self.md_template = Template(self.MARKDOWN_TEMPLATE)
        self.html_template = Template(self.HTML_TEMPLATE)
    
    def generate_markdown(self, result: ScanResult) -> str:
        """生成 Markdown 格式报告"""
        return self.md_template.render(
            result=result,
            now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    
    def generate_json(self, result: ScanResult) -> str:
        """生成 JSON 格式报告"""
        report_data = {
            "scan_id": result.scan_id,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "source_type": result.source_type.value,
            "source_info": result.source_info,
            "summary": {
                "total_files": result.summary.total_files,
                "total_lines": result.summary.total_lines,
                "fatal_count": result.summary.fatal_count,
                "error_count": result.summary.error_count,
                "warning_count": result.summary.warning_count,
                "info_count": result.summary.info_count,
                "total_violations": result.summary.total_violations,
                "blocking_violations": result.summary.blocking_violations
            },
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "rule_name": v.rule_name,
                    "severity": v.severity,
                    "category": v.category,
                    "message": v.message,
                    "file_path": v.file_path,
                    "location": {
                        "line_number": v.location.line_number,
                        "column_start": v.location.column_start,
                        "column_end": v.location.column_end,
                        "matched_text": v.location.matched_text
                    },
                    "matched_content": v.matched_content,
                    "suggested_fix": v.suggested_fix,
                    "require_approval": v.require_approval,
                    "docs_link": v.docs_link
                }
                for v in result.violations
            ],
            "has_blocking_violations": result.has_blocking_violations()
        }
        return json.dumps(report_data, indent=2, ensure_ascii=False)
    
    def generate_html(self, result: ScanResult) -> str:
        """生成 HTML 格式报告"""
        return self.html_template.render(
            result=result,
            now=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
    
    def save_report(
        self, 
        result: ScanResult, 
        output_path: str,
        format: str = "markdown"
    ) -> str:
        """
        保存报告到文件
        
        Args:
            result: 扫描结果
            output_path: 输出文件路径
            format: 报告格式 (markdown/json/html)
            
        Returns:
            str: 保存的文件路径
        """
        output_path = Path(output_path)
        
        if format == "markdown":
            content = self.generate_markdown(result)
            if not output_path.suffix:
                output_path = output_path.with_suffix('.md')
        elif format == "json":
            content = self.generate_json(result)
            if not output_path.suffix:
                output_path = output_path.with_suffix('.json')
        elif format == "html":
            content = self.generate_html(result)
            if not output_path.suffix:
                output_path = output_path.with_suffix('.html')
        else:
            raise ValueError(f"不支持的报告格式: {format}")
        
        # 确保目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"报告已保存: {output_path}")
        return str(output_path)
    
    def print_console_report(self, result: ScanResult) -> None:
        """打印控制台报告（使用 Rich）"""
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        from rich.text import Text
        
        console = Console()
        
        # 标题
        console.print(Panel.fit(
            f"[bold blue]Gatekeeper 代码审核报告[/bold blue]\n"
            f"扫描ID: {result.scan_id} | 时间: {result.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            title="🔒",
            border_style="blue"
        ))
        
        # 统计表格
        table = Table(title="风险统计")
        table.add_column("风险等级", style="cyan")
        table.add_column("数量", justify="right")
        table.add_column("状态", style="bold")
        
        severities = [
            ("🔴 Fatal", result.summary.fatal_count, "red"),
            ("🟠 Error", result.summary.error_count, "orange3"),
            ("🟡 Warning", result.summary.warning_count, "yellow"),
            ("🔵 Info", result.summary.info_count, "blue"),
        ]
        
        for name, count, color in severities:
            status = "❌ 需处理" if count > 0 and color in ["red", "orange3"] else "✅ 通过" if count == 0 else "💡 提示"
            table.add_row(f"[{color}]{name}[/{color}]", str(count), status)
        
        console.print(table)
        
        # 违规详情
        if result.violations:
            console.print(f"\n[bold]发现 {result.summary.total_violations} 个问题:[/bold]\n")
            
            for i, v in enumerate(result.violations, 1):
                severity_color = {
                    "fatal": "red",
                    "error": "orange3",
                    "warning": "yellow",
                    "info": "blue"
                }.get(v.severity, "white")
                
                console.print(Panel(
                    f"[bold]{v.rule_name}[/bold] [{severity_color}]({v.severity.upper()})[/{severity_color}]\n"
                    f"[dim]规则: {v.rule_id} | 文件: {v.file_path or 'N/A'} | 行: {v.location.line_number}[/dim]\n"
                    f"{v.message}\n"
                    f"[dim]违规代码: {v.matched_content[:100]}{'...' if len(v.matched_content) > 100 else ''}[/dim]",
                    border_style=severity_color
                ))
        else:
            console.print("\n[bold green]✅ 未发现违规项，代码审核通过！[/bold green]\n")
        
        # 阻断性警告
        if result.has_blocking_violations():
            console.print(Panel(
                "[bold red]⚠️ 警告: 发现阻断性违规，请修复后再提交代码！[/bold red]",
                border_style="red"
            ))
