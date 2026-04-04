"""
规则测试
"""

import pytest
from gatekeeper_agent.models.rule import (
    Rule, RuleSet, Severity, Category, Trigger, ContextType,
    CascadeCheck, ValidationRule, ViolationResponse, RuleMetadata, FailAction
)
from gatekeeper_agent.rules.builtin_rules import create_builtin_rule_set


class TestRuleModels:
    """规则模型测试类"""
    
    def test_create_rule(self):
        """测试创建规则"""
        rule = Rule(
            rule_id="test-rule-001",
            name="测试规则",
            severity=Severity.ERROR,
            category=Category.SECURITY,
            description="这是一个测试规则",
            triggers=[
                Trigger(
                    pattern=r"test_pattern",
                    language=["python"],
                    context=ContextType.CODE,
                    file_pattern=["*.py"]
                )
            ],
            violation_response=ViolationResponse(
                block_commit=False,
                message="测试消息"
            )
        )
        
        assert rule.rule_id == "test-rule-001"
        assert rule.name == "测试规则"
        assert rule.severity == Severity.ERROR
        assert rule.category == Category.SECURITY
        assert rule.enabled is True
    
    def test_rule_validation(self):
        """测试规则验证"""
        # 无效的 rule_id（没有连字符）
        with pytest.raises(ValueError):
            Rule(
                rule_id="invalid",
                name="无效规则",
                severity=Severity.WARNING,
                category=Category.STYLE,
                description="测试",
                triggers=[Trigger(pattern=r"test")],
                violation_response=ViolationResponse(
                    block_commit=False,
                    message="测试"
                )
            )
    
    def test_rule_set_operations(self):
        """测试规则集操作"""
        rules = [
            Rule(
                rule_id="test-001",
                name="规则1",
                severity=Severity.ERROR,
                category=Category.SECURITY,
                description="测试规则1",
                triggers=[Trigger(pattern=r"pattern1")],
                violation_response=ViolationResponse(block_commit=False, message="msg1")
            ),
            Rule(
                rule_id="test-002",
                name="规则2",
                severity=Severity.WARNING,
                category=Category.PERFORMANCE,
                description="测试规则2",
                enabled=False,
                triggers=[Trigger(pattern=r"pattern2")],
                violation_response=ViolationResponse(block_commit=False, message="msg2")
            ),
            Rule(
                rule_id="test-003",
                name="规则3",
                severity=Severity.FATAL,
                category=Category.SECURITY,
                description="测试规则3",
                triggers=[Trigger(pattern=r"pattern3")],
                violation_response=ViolationResponse(block_commit=False, message="msg3")
            )
        ]
        
        rule_set = RuleSet(
            name="测试规则集",
            description="用于测试",
            version="1.0.0",
            rules=rules
        )
        
        # 测试获取启用的规则
        enabled_rules = rule_set.get_enabled_rules()
        assert len(enabled_rules) == 2
        
        # 测试按分类获取规则
        security_rules = rule_set.get_rules_by_category(Category.SECURITY)
        assert len(security_rules) == 2
        
        # 测试按严重级别获取规则
        fatal_rules = rule_set.get_rules_by_severity(Severity.FATAL)
        assert len(fatal_rules) == 1


class TestBuiltinRules:
    """内置规则测试类"""
    
    def test_builtin_rules_loading(self):
        """测试加载内置规则"""
        rule_set = create_builtin_rule_set()
        
        assert rule_set.name is not None
        assert len(rule_set.rules) > 0
        
        # 检查是否包含关键规则
        rule_ids = [r.rule_id for r in rule_set.rules]
        assert "security-sql-001" in rule_ids  # DELETE 规则
        assert "security-shell-001" in rule_ids  # rm -rf 规则
    
    def test_security_rules_exist(self):
        """测试安全规则存在"""
        rule_set = create_builtin_rule_set()
        
        security_rules = rule_set.get_rules_by_category(Category.SECURITY)
        assert len(security_rules) > 0
        
        # 检查是否有 Fatal 级别的安全规则
        fatal_security = [r for r in security_rules if r.severity == Severity.FATAL]
        assert len(fatal_security) > 0
    
    def test_cascade_checks_exist(self):
        """测试级联检查存在"""
        rule_set = create_builtin_rule_set()
        
        # 查找有级联检查的规则
        rules_with_cascade = [r for r in rule_set.rules if r.cascade_checks]
        assert len(rules_with_cascade) > 0
        
        # 检查级联检查结构
        for rule in rules_with_cascade:
            for check in rule.cascade_checks:
                assert check.name is not None
                assert check.validation is not None
                assert check.fail_action is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
