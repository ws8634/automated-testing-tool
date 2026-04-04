#!/usr/bin/env python3
"""
Gatekeeper 简单测试演示脚本

作者: Claude 3.5 Sonnet (Anthropic)
版本: 0.1.0
创建时间: 2025-03-13

功能: 演示如何使用 Gatekeeper 检测代码中的 rm 命令
      支持控制台输出和文件报告输出
"""

import sys
import os
import argparse
from datetime import datetime

# 添加项目到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gatekeeper_agent.rules.loader import load_builtin_rules
from gatekeeper_agent.core.engine import RuleEngine
from gatekeeper_agent.core.report import ReportGenerator
from gatekeeper_agent.models.scan import CodeSnippet, SourceType


def test_rm_detection(output_path=None, format_type='console'):
    """
    测试检测 rm 命令
    
    场景: 检测代码中是否包含危险的 rm -rf 命令
    
    Args:
        output_path: 报告输出路径，为None时输出到控制台
        format_type: 报告格式 (console/markdown/json/html)
    """
    print("=" * 70)
    print("🔒 Gatekeeper 简单测试 - 检测 rm 命令")
    print("=" * 70)
    
    # 1. 加载内置规则
    print("\n📋 步骤1: 加载内置规则...")
    rule_set = load_builtin_rules()
    print(f"   ✓ 已加载 {len(rule_set.rules)} 条规则")
    
    # 显示安全相关的规则
    security_rules = [r for r in rule_set.rules if "security" in r.rule_id]
    print(f"   ✓ 其中安全规则 {len(security_rules)} 条")
    
    # 2. 创建规则引擎
    print("\n⚙️  步骤2: 初始化规则引擎...")
    engine = RuleEngine(rule_set)
    print("   ✓ 引擎初始化完成")
    
    # 3. 准备测试代码 - 包含 rm 命令
    print("\n📝 步骤3: 准备测试代码...")
    test_code = '''#!/bin/bash
# 这是一个清理脚本
echo "开始清理..."

# 危险的命令 - 应该被检测到
rm -rf /tmp/data
rm -rf /

# 安全的命令 - 不应该被检测
echo "清理完成"
'''
    print("   测试代码内容:")
    print("   " + "-" * 50)
    for i, line in enumerate(test_code.split('\n'), 1):
        print(f"   {i:2}: {line}")
    print("   " + "-" * 50)
    
    # 4. 创建代码片段
    snippet = CodeSnippet(
        content=test_code,
        language="shell",
        file_path="cleanup.sh",
        line_start=1,
        line_end=len(test_code.split('\n')),
        source_type=SourceType.FILE
    )
    
    # 5. 执行扫描
    print("\n🔍 步骤4: 执行代码扫描...")
    result = engine.scan(snippet)
    
    # 6. 输出报告
    report_gen = ReportGenerator()
    
    if output_path:
        # 输出到文件
        saved_path = report_gen.save_report(result, output_path, format_type)
        print(f"\n✅ 报告已保存到: {saved_path}")
    else:
        # 输出到控制台
        _print_console_report(result)
    
    # 7. 返回是否有阻断性违规
    if result.has_blocking_violations():
        print("\n❌ 检测到阻断性违规！")
        return 1
    else:
        print("\n✅ 扫描完成，未发现阻断性问题")
        return 0


def scan_project(project_path, output_path=None, format_type='console'):
    """
    扫描项目代码
    
    Args:
        project_path: 要扫描的项目路径
        output_path: 报告输出路径，为None时输出到控制台
        format_type: 报告格式 (console/markdown/json/html)
    """
    print("\n" + "=" * 70)
    print(f"🔍 扫描项目: {project_path}")
    print("=" * 70)
    
    if not os.path.exists(project_path):
        print(f"❌ 路径不存在: {project_path}")
        return 1
    
    # 加载规则
    rule_set = load_builtin_rules()
    engine = RuleEngine(rule_set)
    
    # 扫描目录
    from gatekeeper_agent.parsers.file_parser import FileParser
    parser = FileParser()
    
    print(f"\n📁 正在扫描目录: {project_path}")
    snippets = parser.parse_directory(project_path)
    print(f"   找到 {len(snippets)} 个文件")
    
    if not snippets:
        print("   没有可扫描的文件")
        return 0
    
    # 批量扫描
    print("\n🔍 开始扫描文件...")
    result = engine.scan_batch(snippets)
    
    # 输出报告
    report_gen = ReportGenerator()
    
    if output_path:
        # 输出到文件
        saved_path = report_gen.save_report(result, output_path, format_type)
        print(f"\n✅ 报告已保存到: {saved_path}")
    else:
        # 输出到控制台
        _print_console_report(result)
    
    return 0 if not result.has_blocking_violations() else 1


def _print_console_report(result):
    """打印控制台报告"""
    print("\n" + "=" * 70)
    print("📊 扫描结果汇总")
    print("=" * 70)
    print(f"扫描ID: {result.scan_id}")
    print(f"扫描文件: {result.summary.total_files} 个")
    print(f"扫描行数: {result.summary.total_lines} 行")
    print(f"违规总数: {result.summary.total_violations} 个")
    print(f"  - 🔴 Fatal:   {result.summary.fatal_count}")
    print(f"  - 🟠 Error:   {result.summary.error_count}")
    print(f"  - 🟡 Warning: {result.summary.warning_count}")
    print(f"  - 🔵 Info:    {result.summary.info_count}")
    
    if result.violations:
        print("\n" + "-" * 70)
        print("🚨 发现的违规项详情:")
        print("-" * 70)
        for i, v in enumerate(result.violations, 1):
            print(f"\n  [{i}] {v.rule_name}")
            print(f"      规则ID: {v.rule_id}")
            print(f"      风险等级: {v.severity.upper()}")
            print(f"      文件: {v.file_path or 'N/A'}")
            print(f"      位置: 第 {v.location.line_number} 行")
            print(f"      匹配内容: {v.matched_content}")
            
            # 显示完整行内容
            if hasattr(v.location, 'matched_text') and v.location.matched_text:
                print(f"      代码行: {v.location.matched_text}")
            
            if v.cascade_results:
                print(f"      级联检查:")
                for cr in v.cascade_results:
                    status = "✓ 通过" if cr.passed else "✗ 失败"
                    print(f"        - {cr.check_name}: {status}")
    else:
        print("\n✅ 未发现违规项")
    
    print("\n" + "=" * 70)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Gatekeeper 代码审核测试工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 基本测试（控制台输出）
  python test_demo.py
  
  # 生成 Markdown 报告
  python test_demo.py -o report.md -f markdown
  
  # 扫描其他项目并生成 HTML 报告
  python test_demo.py /path/to/project -o report.html -f html
  
  # 扫描项目并生成 JSON 报告（适合 CI/CD）
  python test_demo.py /path/to/project -o report.json -f json
        '''
    )
    
    parser.add_argument(
        'project_path',
        nargs='?',
        default=None,
        help='要扫描的项目路径（可选，默认为内置测试）'
    )
    
    parser.add_argument(
        '-o', '--output',
        default=None,
        help='报告输出路径（如 report.md, report.html）'
    )
    
    parser.add_argument(
        '-f', '--format',
        choices=['console', 'markdown', 'json', 'html'],
        default='console',
        help='报告格式（默认: console）'
    )
    
    args = parser.parse_args()
    
    # 根据参数执行相应功能
    if args.project_path:
        exit_code = scan_project(args.project_path, args.output, args.format)
    else:
        exit_code = test_rm_detection(args.output, args.format)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
