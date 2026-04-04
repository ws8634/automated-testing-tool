#!/usr/bin/env python3
"""
测试 rm 规则改进

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


def test_rm_variations():
    """测试各种 rm 命令变体"""
    
    test_cases = [
        ("rm -rf /tmp/data", "shell", "应该检测: rm -rf"),
        ("rm -f file.txt", "shell", "应该检测: rm -f"),
        ("rm -r directory", "shell", "应该检测: rm -r"),
        ("rm --force file", "shell", "应该检测: rm --force"),
        ("rm --recursive dir", "shell", "应该检测: rm --recursive"),
        ("rm file.txt", "shell", "不应该检测: 普通 rm"),
        ("os.system('rm -rf /tmp')", "python", "应该检测: Python中的 rm -rf"),
        ("os.system('rm -f file')", "python", "应该检测: Python中的 rm -f"),
        ("subprocess.call(['rm', '-rf', '/tmp'])", "python", "应该检测: subprocess rm"),
    ]
    
    print("=" * 70)
    print("🔍 测试 rm 规则 - 各种变体")
    print("=" * 70)
    
    rule_set = load_builtin_rules()
    engine = RuleEngine(rule_set)
    
    for code, language, description in test_cases:
        print(f"\n📝 测试: {description}")
        print(f"   代码: {code}")
        
        # 根据语言选择合适的文件扩展名
        ext = 'sh' if language == 'shell' else 'py'
        snippet = CodeSnippet(
            content=code,
            language=language,
            file_path=f"test.{ext}",
            line_start=1,
            line_end=1,
            source_type=SourceType.FILE
        )
        
        result = engine.scan(snippet)
        
        if result.violations:
            print(f"   ✅ 检测到 {len(result.violations)} 个违规")
            for v in result.violations:
                print(f"      - {v.rule_name}: {v.matched_content}")
        else:
            print(f"   ❌ 未检测到违规")


if __name__ == "__main__":
    test_rm_variations()
