"""
报告 API
"""

from typing import List, Optional
from pathlib import Path
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from gatekeeper_agent.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ReportSummary(BaseModel):
    """报告摘要"""
    report_id: str
    scan_id: str
    created_at: str
    source_type: str
    total_files: int
    total_violations: int
    fatal_count: int
    error_count: int
    warning_count: int
    has_blocking: bool


class ReportListResponse(BaseModel):
    """报告列表响应"""
    total: int
    reports: List[ReportSummary]


# 模拟报告存储（实际应使用数据库）
reports_db = {}


def _generate_report_id() -> str:
    """生成报告ID"""
    return f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(reports_db)}"


@router.get("", response_model=ReportListResponse)
async def list_reports(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    has_blocking: Optional[bool] = None
):
    """获取报告列表"""
    try:
        reports = []
        for report_id, report in reports_db.items():
            if has_blocking is not None:
                if report.get("has_blocking") != has_blocking:
                    continue
            reports.append(ReportSummary(
                report_id=report_id,
                scan_id=report.get("scan_id", ""),
                created_at=report.get("created_at", ""),
                source_type=report.get("source_type", ""),
                total_files=report.get("total_files", 0),
                total_violations=report.get("total_violations", 0),
                fatal_count=report.get("fatal_count", 0),
                error_count=report.get("error_count", 0),
                warning_count=report.get("warning_count", 0),
                has_blocking=report.get("has_blocking", False),
            ))
        
        # 按时间倒序排序
        reports.sort(key=lambda x: x.created_at, reverse=True)
        
        total = len(reports)
        reports = reports[offset:offset + limit]
        
        return ReportListResponse(total=total, reports=reports)
    except Exception as e:
        logger.error(f"获取报告列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}")
async def get_report(report_id: str):
    """获取报告详情"""
    try:
        if report_id not in reports_db:
            raise HTTPException(status_code=404, detail=f"报告不存在: {report_id}")
        
        return reports_db[report_id]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取报告详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}/html", response_class=HTMLResponse)
async def get_report_html(report_id: str):
    """获取报告 HTML 内容"""
    try:
        if report_id not in reports_db:
            raise HTTPException(status_code=404, detail=f"报告不存在: {report_id}")
        
        report = reports_db[report_id]
        html_content = report.get("html_content", "")
        
        if not html_content:
            # 生成简单的 HTML 报告
            html_content = _generate_simple_html_report(report)
        
        return HTMLResponse(content=html_content)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取报告 HTML 失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _generate_simple_html_report(report: dict) -> str:
    """生成简单的 HTML 报告"""
    violations = report.get("violations", [])
    
    violations_html = ""
    for v in violations:
        severity_color = {
            "fatal": "#dc3545",
            "error": "#fd7e14",
            "warning": "#ffc107",
            "info": "#17a2b8",
        }.get(v.get("severity", ""), "#666")
        
        violations_html += f"""
        <div style="border-left: 4px solid {severity_color}; padding: 15px; margin: 10px 0; background: #f8f9fa;">
            <h4 style="margin: 0 0 10px 0;">{v.get('rule_name', '')}</h4>
            <p style="margin: 5px 0; color: #666;">
                <strong>规则:</strong> {v.get('rule_id', '')} | 
                <strong>等级:</strong> {v.get('severity', '').upper()} | 
                <strong>文件:</strong> {v.get('file_path', 'N/A')}
            </p>
            <p style="margin: 10px 0;">{v.get('message', '')}</p>
            <pre style="background: #2d2d2d; color: #f8f8f2; padding: 10px; border-radius: 4px; overflow-x: auto;">
{v.get('matched_content', '')}</pre>
        </div>
        """
    
    return f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gatekeeper 报告 - {report.get('scan_id', '')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                background: #f5f5f5; padding: 20px; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
        h1 {{ color: #333; margin-bottom: 20px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
        .stat {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #667eea; }}
        .stat-label {{ color: #666; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔒 Gatekeeper 代码审核报告</h1>
        <p style="color: #666;">扫描ID: {report.get('scan_id', '')}</p>
        <p style="color: #666;">时间: {report.get('created_at', '')}</p>
        
        <div class="summary">
            <div class="stat">
                <div class="stat-value">{report.get('total_files', 0)}</div>
                <div class="stat-label">扫描文件</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: #dc3545;">{report.get('fatal_count', 0)}</div>
                <div class="stat-label">Fatal</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: #fd7e14;">{report.get('error_count', 0)}</div>
                <div class="stat-label">Error</div>
            </div>
            <div class="stat">
                <div class="stat-value" style="color: #ffc107;">{report.get('warning_count', 0)}</div>
                <div class="stat-label">Warning</div>
            </div>
        </div>
        
        <h2 style="margin-top: 30px;">违规详情</h2>
        {violations_html if violations else '<p style="color: #28a745; text-align: center; padding: 40px;">✅ 未发现违规项</p>'}
    </div>
</body>
</html>
    """


@router.post("/save")
async def save_report(scan_result: dict):
    """保存扫描报告"""
    try:
        report_id = _generate_report_id()
        
        reports_db[report_id] = {
            "report_id": report_id,
            "scan_id": scan_result.get("scan_id", ""),
            "created_at": datetime.now().isoformat(),
            "source_type": scan_result.get("source_type", ""),
            "total_files": scan_result.get("summary", {}).get("total_files", 0),
            "total_violations": scan_result.get("summary", {}).get("total_violations", 0),
            "fatal_count": scan_result.get("summary", {}).get("fatal_count", 0),
            "error_count": scan_result.get("summary", {}).get("error_count", 0),
            "warning_count": scan_result.get("summary", {}).get("warning_count", 0),
            "info_count": scan_result.get("summary", {}).get("info_count", 0),
            "has_blocking": scan_result.get("has_blocking_violations", False),
            "violations": scan_result.get("violations", []),
        }
        
        return {"report_id": report_id, "message": "报告保存成功"}
    except Exception as e:
        logger.error(f"保存报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{report_id}")
async def delete_report(report_id: str):
    """删除报告"""
    try:
        if report_id not in reports_db:
            raise HTTPException(status_code=404, detail=f"报告不存在: {report_id}")
        
        del reports_db[report_id]
        return {"message": "报告已删除", "report_id": report_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{report_id}/export")
async def export_report(report_id: str, format: str = "html"):
    """导出报告为文件"""
    try:
        if report_id not in reports_db:
            raise HTTPException(status_code=404, detail=f"报告不存在: {report_id}")
        
        report = reports_db[report_id]
        
        if format == "html":
            html_content = _generate_simple_html_report(report)
            return HTMLResponse(
                content=html_content,
                headers={"Content-Disposition": f"attachment; filename=report-{report_id}.html"}
            )
        elif format == "json":
            import json
            return {
                "content": json.dumps(report, indent=2, ensure_ascii=False),
                "filename": f"report-{report_id}.json"
            }
        else:
            raise HTTPException(status_code=400, detail=f"不支持的格式: {format}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
