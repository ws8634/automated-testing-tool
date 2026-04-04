"""
性能规则

作者: Claude 3.5 Sonnet (Anthropic)
版本: 0.1.0
创建时间: 2026-03-14

包含规则:
    1. performance-db-001: 潜在的 N+1 查询问题
"""

from typing import List
from gatekeeper_agent.models.rule import (
    Rule, Severity, Category, Trigger, ContextType,
    ViolationResponse, RuleMetadata
)


def get_performance_rules() -> List[Rule]:
    """获取性能规则列表"""
    return [
        _get_n_plus_one_rule(),
    ]


def _get_n_plus_one_rule() -> Rule:
    """潜在的 N+1 查询问题"""
    return Rule(
        rule_id="performance-db-001",
        name="潜在的 N+1 查询问题",
        severity=Severity.WARNING,
        category=Category.PERFORMANCE,
        description="检测到循环中可能存在数据库查询，可能导致 N+1 查询问题",
        triggers=[
            Trigger(
                pattern=r"for\s+\w+\s+in\s+\w+:\s*\n\s+.*\.(get|filter|query|select)",
                language=["python"],
                context=ContextType.CODE,
                file_pattern=["*.py"]
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【性能提示】检测到潜在的 N+1 查询问题 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "考虑使用 select_related 或 prefetch_related 优化查询",
            suggested_fix="# 使用 prefetch_related 优化\nusers = User.objects.prefetch_related('orders').all()\nfor user in users:\n    for order in user.orders.all():  # 不会产生额外查询\n        pass",
            require_approval=None
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="performance-team",
            tags=["performance", "database", "n+1"]
        )
    )
