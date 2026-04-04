#!/usr/bin/env python3
"""
测试截图中的代码检测

作者: Claude 3.5 Sonnet (Anthropic)
版本: 0.1.0
创建时间: 2025-03-13
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gatekeeper_agent.rules.loader import load_builtin_rules
from gatekeeper_agent.core.engine import RuleEngine
from gatekeeper_agent.models.scan import CodeSnippet, SourceType


def test_screenshot_code():
    """测试截图中的代码"""
    
    # 截图中的代码
    test_code = '''
@click.option('--format', '-f', 'format_', default='console',
              type=click.Choice(['console', 'markdown', 'json', 'html']),
              help='报告格式')
@click.option('--no-builtin', is_flag=True, help='不使用内置规则')
@click.option('--rm', '-rm', default=None, help='自定义规则目录')
@click.pass_context
def staged(
    ctx: click.Context,
    path: str,
    output: Optional[str],
    format_: str,
    no_builtin: bool,
    rules_dir: Optional[str]
) -> None:
    """扫描暂存区（Staged）变更"""
    try:
        # 加载规则
        console.print("[blue]正在加载规则...[/blue]")
        rule_set = load_rules(builtin=not no_builtin, custom_dir=rules_dir)
'''
    
    print("=" * 70)
    print("🔍 测试截图中的代码")
    print("=" * 70)
    print("\n测试代码内容:")
    print(test_code)
    
    rule_set = load_builtin_rules()
    engine = RuleEngine(rule_set)
    
    snippet = CodeSnippet(
        content=test_code,
        language="python",
        file_path="cli.py",
        line_start=1,
        line_end=len(test_code.split('\n')),
        source_type=SourceType.FILE
    )
    
    result = engine.scan(snippet)
    
    print(f"\n📊 扫描结果:")
    print(f"   违规数: {result.summary.total_violations}")
    
    if result.violations:
        print(f"\n🚨 发现的违规项:")
        for i, v in enumerate(result.violations, 1):
            print(f"   [{i}] {v.rule_name}")
            print(f"       位置: 第 {v.location.line_number} 行")
            print(f"       匹配: {v.matched_content}")
    else:
        print("\n✅ 未发现违规")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    test_screenshot_code()
