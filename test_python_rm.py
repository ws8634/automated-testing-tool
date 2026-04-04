#!/usr/bin/env python3
"""
测试 Python 文件中的 rm 检测

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


def test_python_rm():
    """测试 Python 文件中的 rm 检测"""
    
    test_cases = [
        # 应该检测的 - 字符串中包含 rm 命令
        ('command = "rm -rf /tmp/data"', "字符串赋值 rm -rf - 应该检测"),
        ('cmd = "rm -f file.txt"', "字符串赋值 rm -f - 应该检测"),
        ('os.system("rm -rf /tmp")', "os.system 调用 - 应该检测"),
        ('subprocess.call(["rm", "-rf", "/tmp"])', "subprocess 调用 - 应该检测"),
        
        # 不应该检测的 - 普通字符串
        ('print("使用 rm -rf 命令要小心")', "提示信息中的 rm - 不应该检测"),
        ('text = "rm -rf 是危险命令"', "文档字符串 - 不应该检测"),
    ]
    
    print("=" * 70)
    print("🔍 测试 Python 文件中的 rm 检测")
    print("=" * 70)
    
    rule_set = load_builtin_rules()
    engine = RuleEngine(rule_set)
    
    detected_count = 0
    for code, description in test_cases:
        print(f"\n📝 {description}")
        print(f"   代码: {code}")
        
        snippet = CodeSnippet(
            content=code,
            language="python",
            file_path="test.py",
            line_start=1,
            line_end=1,
            source_type=SourceType.FILE
        )
        
        result = engine.scan(snippet)
        
        if result.violations:
            print(f"   ✅ 检测到 {len(result.violations)} 个违规")
            for v in result.violations:
                print(f"      - {v.rule_id}: {v.matched_content}")
            detected_count += 1
        else:
            print(f"   ❌ 未检测到违规")
    
    print("\n" + "=" * 70)
    print(f"📊 测试结果: {detected_count}/{len(test_cases)} 个测试用例检测到违规")
    print("=" * 70)


if __name__ == "__main__":
    test_python_rm()
