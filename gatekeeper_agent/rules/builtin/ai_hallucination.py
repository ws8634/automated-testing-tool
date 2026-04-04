"""
AI 幻觉规则

作者: Claude 3.5 Sonnet (Anthropic)
版本: 0.1.0
创建时间: 2026-03-14

包含规则:
    1. ai-hallucination-001: 可能存在幻觉的 API 调用
    2. ai-hallucination-002: 逻辑矛盾的代码
"""

from typing import List
from gatekeeper_agent.models.rule import (
    Rule, Severity, Category, Trigger, ContextType,
    ViolationResponse, RuleMetadata
)


def get_ai_hallucination_rules() -> List[Rule]:
    """获取AI幻觉规则列表"""
    return [
        _get_hallucination_api_rule(),
        _get_logic_contradiction_rule(),
    ]


def _get_hallucination_api_rule() -> Rule:
    """可能存在幻觉的 API 调用"""
    return Rule(
        rule_id="ai-hallucination-001",
        name="可能存在幻觉的 API 调用",
        severity=Severity.WARNING,
        category=Category.AI_HALLUCINATION,
        description="检测到可能不存在的 API 调用或方法",
        triggers=[
            Trigger(
                pattern=r"(OpenAI|ChatGPT|GPT-4|Claude|Gemini)\s*\.\s*\w+",
                language=["python", "javascript"],
                context=ContextType.CODE,
                file_pattern=["*.py", "*.js", "*.ts"]
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【AI 幻觉检查】检测到可能的幻觉 API 调用 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "匹配内容: {match_content}\n"
                    "请验证该 API 是否真实存在！",
            suggested_fix=None,
            require_approval=None
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="ai-team",
            ai_code_only=True,
            tags=["ai", "hallucination", "api"]
        )
    )


def _get_logic_contradiction_rule() -> Rule:
    """逻辑矛盾的代码"""
    return Rule(
        rule_id="ai-hallucination-002",
        name="逻辑矛盾的代码",
        severity=Severity.WARNING,
        category=Category.AI_HALLUCINATION,
        description="检测到可能存在逻辑矛盾的代码",
        triggers=[
            Trigger(
                pattern=r"if\s+\w+\s*:\s*\n\s+.*\n\s+if\s+not\s+\w+\s*:",
                language=["python"],
                context=ContextType.CODE,
                file_pattern=["*.py"]
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【AI 幻觉检查】检测到可能的逻辑矛盾 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "请检查代码逻辑是否正确！",
            suggested_fix=None,
            require_approval=None
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="ai-team",
            ai_code_only=True,
            tags=["ai", "hallucination", "logic"]
        )
    )
