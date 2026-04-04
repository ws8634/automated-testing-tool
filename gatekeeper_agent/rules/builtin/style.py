"""
代码规范规则

作者: Claude 3.5 Sonnet (Anthropic)
版本: 0.1.0
创建时间: 2026-03-14

包含规则:
    1. style-docstring-001: 公共函数缺少文档字符串 (Info)
    2. style-comment-001: 复杂逻辑缺少注释 (Info)
    3. style-todo-001: 代码中包含 TODO (Info)
"""

from typing import List
from gatekeeper_agent.models.rule import (
    Rule, Severity, Category, Trigger, ContextType,
    ViolationResponse, RuleMetadata
)


def get_style_rules() -> List[Rule]:
    """获取代码规范规则列表"""
    return [
        _get_missing_docstring_rule(),
        _get_missing_comment_rule(),
        _get_todo_rule(),
    ]


def _get_missing_docstring_rule() -> Rule:
    """公共函数缺少文档字符串"""
    return Rule(
        rule_id="style-docstring-001",
        name="公共函数缺少文档字符串",
        severity=Severity.INFO,
        category=Category.STYLE,
        description="公共函数和类应该包含文档字符串说明功能",
        triggers=[
            Trigger(
                pattern=r"^def\s+[a-zA-Z_][a-zA-Z0-9_]*\s*\([^)]*\)(?!\s*->)\s*:\s*\n(?!\s+\"\"\"|\s+''')",
                language=["python"],
                context=ContextType.CODE,
                file_pattern=["*.py"]
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【规范提示】公共函数建议添加文档字符串 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "文档字符串有助于代码理解和维护",
            suggested_fix='def my_function():\n    """\n    函数功能说明\n    \n    Returns:\n        返回值说明\n    """\n    pass',
            require_approval=None
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="code-quality-team",
            tags=["documentation", "style", "info"]
        )
    )


def _get_missing_comment_rule() -> Rule:
    """复杂逻辑缺少注释"""
    return Rule(
        rule_id="style-comment-001",
        name="复杂逻辑建议添加注释",
        severity=Severity.INFO,
        category=Category.STYLE,
        description="复杂算法或业务逻辑建议添加注释说明",
        triggers=[
            Trigger(
                pattern=r"(for\s+.+\s+in\s+.+:|while\s+.+:).{0,50}\n\s+(for\s+.+\s+in\s+.+:|while\s+.+:|if\s+.+:)",
                language=["python"],
                context=ContextType.CODE,
                file_pattern=["*.py"]
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【规范提示】嵌套循环建议添加注释 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "复杂逻辑添加注释有助于维护",
            suggested_fix="# 遍历用户列表并计算订单总额\nfor user in users:\n    # 获取用户订单\n    orders = get_orders(user)\n    for order in orders:\n        process(order)",
            require_approval=None
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="code-quality-team",
            tags=["comment", "style", "info"]
        )
    )


def _get_todo_rule() -> Rule:
    """代码中包含 TODO"""
    return Rule(
        rule_id="style-todo-001",
        name="代码中包含 TODO 标记",
        severity=Severity.INFO,
        category=Category.STYLE,
        description="检测到 TODO/FIXME 标记，建议跟踪处理",
        triggers=[
            Trigger(
                pattern=r"#\s*(TODO|FIXME|XXX|HACK)",
                language=["python", "javascript", "go", "java", "shell"],
                context=ContextType.CODE,
                file_pattern=["*.py", "*.js", "*.go", "*.java", "*.sh"]
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【提示】代码中包含 {match_content} 标记 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "建议跟踪处理或创建 Issue",
            suggested_fix=None,
            require_approval=None
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="code-quality-team",
            tags=["todo", "style", "info"]
        )
    )
