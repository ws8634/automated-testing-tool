"""
内置规则分类模块

作者: Claude 3.5 Sonnet (Anthropic)
版本: 0.1.0
创建时间: 2026-03-14

规则分类:
    1. high_risk - 高危操作规则 (FATAL/ERROR级别)
    2. security - 安全规则 (FATAL/ERROR/WARNING/INFO级别)
    3. business - 业务规则
    4. performance - 性能规则
    5. ai_hallucination - AI幻觉规则
    6. supply_chain - 供应链安全规则 (基于OpenClaw安全建议)
    7. style - 代码规范规则 (INFO级别)
"""

from gatekeeper_agent.rules.builtin.high_risk import get_high_risk_rules
from gatekeeper_agent.rules.builtin.security import get_security_rules
from gatekeeper_agent.rules.builtin.business import get_business_rules
from gatekeeper_agent.rules.builtin.performance import get_performance_rules
from gatekeeper_agent.rules.builtin.ai_hallucination import get_ai_hallucination_rules
from gatekeeper_agent.rules.builtin.supply_chain import get_supply_chain_rules

__all__ = [
    "get_high_risk_rules",
    "get_security_rules",
    "get_business_rules",
    "get_performance_rules",
    "get_ai_hallucination_rules",
    "get_supply_chain_rules",
]
