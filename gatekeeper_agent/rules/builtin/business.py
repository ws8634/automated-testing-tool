"""
业务规则

作者: Claude 3.5 Sonnet (Anthropic)
版本: 0.1.0
创建时间: 2026-03-14

包含规则:
    1. business-auth-001: 接口权限校验缺失
"""

from typing import List
from gatekeeper_agent.models.rule import (
    Rule, Severity, Category, Trigger, ContextType,
    CascadeCheck, ValidationRule, ViolationResponse, RuleMetadata, FailAction
)


def get_business_rules() -> List[Rule]:
    """获取业务规则列表"""
    return [
        _get_auth_check_rule(),
    ]


def _get_auth_check_rule() -> Rule:
    """接口权限校验缺失"""
    return Rule(
        rule_id="business-auth-001",
        name="接口权限校验缺失",
        severity=Severity.ERROR,
        category=Category.BUSINESS,
        description="检测到可能缺少权限校验的接口定义",
        triggers=[
            Trigger(
                pattern=r"@(app\.)?route\s*\([^)]+\)\s*\n\s*def\s+\w+",
                language=["python"],
                context=ContextType.CODE,
                file_pattern=["*.py"]
            ),
            Trigger(
                pattern=r"(router\.|app\.)\.(get|post|put|delete)\s*\([^)]+\)",
                language=["javascript"],
                context=ContextType.CODE,
                file_pattern=["*.js", "*.ts"]
            )
        ],
        cascade_checks=[
            CascadeCheck(
                name="权限装饰器检查",
                description="检查是否添加了权限校验装饰器",
                validation=ValidationRule(
                    must_contain=[r"@(require_auth|login_required|authenticate|permission|authorize)"]
                ),
                fail_action=FailAction.WARN
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【业务警告】接口可能缺少权限校验 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "请确保敏感接口已添加权限校验！",
            suggested_fix="@require_auth\n@app.route('/api/protected')\ndef protected_route():\n    pass",
            require_approval="tech-lead"
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="business-team",
            tags=["auth", "permission", "api"]
        )
    )
