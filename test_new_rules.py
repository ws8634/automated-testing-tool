#!/usr/bin/env python3
"""
测试新增的高危命令规则

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


def test_new_rules():
    """测试新增规则"""
    
    test_cases = [
        # sudo 规则
        ("sudo rm -rf /tmp/data", "shell", "sudo rm - 应该检测"),
        ("sudo dd if=/dev/zero of=/dev/sdb", "shell", "sudo dd - 应该检测"),
        ("sudo mkfs.ext4 /dev/sdb1", "shell", "sudo mkfs - 应该检测"),
        ("sudo reboot", "shell", "sudo reboot - 应该检测"),
        
        # dd 规则
        ("dd if=/dev/zero of=/dev/sdb bs=4M", "shell", "dd 磁盘操作 - 应该检测"),
        ("dd if=/path/to/file of=/path/to/dest", "shell", "dd 普通文件 - 不应该检测"),
        
        # mkfs 规则
        ("mkfs.ext4 /dev/sdb1", "shell", "mkfs.ext4 - 应该检测"),
        ("mkfs -t ext4 /dev/sdc2", "shell", "mkfs -t - 应该检测"),
        
        # kubectl delete 规则
        ("kubectl delete pod my-pod", "shell", "kubectl delete pod - 应该检测"),
        ("kubectl delete deployment my-app", "shell", "kubectl delete deployment - 应该检测"),
        ("kubectl delete -f config.yaml", "shell", "kubectl delete -f - 应该检测"),
        ("kubectl delete --all", "shell", "kubectl delete --all - 应该检测"),
        
        # Docker 规则
        ("docker rm -f container", "shell", "docker rm -f - 应该检测"),
        ("docker rmi -f image", "shell", "docker rmi -f - 应该检测"),
        ("docker system prune -f", "shell", "docker system prune -f - 应该检测"),
        ("docker container prune -f", "shell", "docker container prune -f - 应该检测"),
    ]
    
    print("=" * 70)
    print("🔍 测试新增高危命令规则")
    print("=" * 70)
    
    rule_set = load_builtin_rules()
    engine = RuleEngine(rule_set)
    
    print(f"\n📋 已加载 {len(rule_set.rules)} 条规则")
    
    # 统计高危规则
    high_risk_rules = [r for r in rule_set.rules if r.rule_id.startswith("security-shell") or r.rule_id.startswith("security-k8s") or r.rule_id.startswith("security-docker")]
    print(f"   其中高危操作规则: {len(high_risk_rules)} 条")
    
    detected_count = 0
    for code, language, description in test_cases:
        print(f"\n📝 {description}")
        print(f"   代码: {code}")
        
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
                print(f"      - {v.rule_id}: {v.rule_name}")
            detected_count += 1
        else:
            print(f"   ❌ 未检测到违规")
    
    print("\n" + "=" * 70)
    print(f"📊 测试结果: {detected_count}/{len(test_cases)} 个测试用例检测到违规")
    print("=" * 70)


if __name__ == "__main__":
    test_new_rules()
