"""
规则数据模型定义

作者: Claude 3.5 Sonnet (Anthropic)
版本: 0.1.0
创建时间: 2026-03-14

功能目标:
    - 定义规则相关的数据模型
    - 支持 Pydantic 数据验证
    - 提供规则集的查询和管理方法

对应需求:
    1. 标准化规则引擎 - 规则结构定义
    2. 规则分类管理 - security/business/performance/ai_hallucination
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class Severity(str, Enum):
    """风险等级"""
    FATAL = "fatal"      # 阻断提交
    ERROR = "error"      # 需审批
    WARNING = "warning"  # 仅提示
    INFO = "info"        # 仅记录


class Category(str, Enum):
    """规则分类"""
    SECURITY = "security"
    BUSINESS = "business"
    PERFORMANCE = "performance"
    AI_HALLUCINATION = "ai_hallucination"
    STYLE = "style"


class ContextType(str, Enum):
    """检测上下文类型"""
    CODE = "code"    # 完整代码
    DIFF = "diff"    # 代码Diff
    CONFIG = "config"  # 配置文件


class Trigger(BaseModel):
    """规则触发条件"""
    pattern: str = Field(..., description="正则表达式匹配规则")
    language: List[str] = Field(default_factory=list, description="适用编程语言")
    context: ContextType = Field(default=ContextType.CODE, description="检测上下文")
    file_pattern: List[str] = Field(default_factory=list, description="适用文件后缀模式")


class ValidationRule(BaseModel):
    """级联检查验证规则"""
    must_contain: List[str] = Field(default_factory=list, description="必须存在的代码模式")
    must_not_contain: List[str] = Field(default_factory=list, description="禁止存在的代码模式")
    ast_check: Optional[str] = Field(None, description="AST节点类型检查规则")
    llm_intent_check: Optional[str] = Field(None, description="PRD意图匹配校验")


class FailAction(str, Enum):
    """级联检查失败动作"""
    BLOCK = "block"
    WARN = "warn"
    UPGRADE_SEVERITY = "upgrade_severity"


class CascadeCheck(BaseModel):
    """级联检查配置"""
    name: str = Field(..., description="关联检查名称")
    description: str = Field(..., description="级联检查的业务逻辑说明")
    validation: ValidationRule = Field(..., description="验证规则")
    fail_action: FailAction = Field(default=FailAction.WARN, description="检查失败后的动作")


class ViolationResponse(BaseModel):
    """违规响应配置"""
    block_commit: bool = Field(default=False, description="是否直接阻断Git提交")
    message: str = Field(..., description="给开发者的提示信息")
    suggested_fix: Optional[str] = Field(None, description="修复代码示例")
    require_approval: Optional[str] = Field(None, description="需审批角色")
    docs_link: Optional[str] = Field(None, description="规则说明文档链接")


class RuleMetadata(BaseModel):
    """规则元数据"""
    version: str = Field(default="1.0", description="规则版本")
    author: str = Field(default="security-team", description="规则维护人")
    ai_code_only: bool = Field(default=False, description="是否仅针对AI生成代码生效")
    tags: List[str] = Field(default_factory=list, description="规则标签")


class Rule(BaseModel):
    """
    审核规则模型
    
    规则ID格式: {分类}-{场景}-{序号}
    示例: security-sql-001, business-auth-001
    """
    rule_id: str = Field(..., description="唯一标识符，格式：{分类}-{场景}-{序号}")
    name: str = Field(..., description="规则名称")
    severity: Severity = Field(..., description="风险等级")
    category: Category = Field(..., description="规则分类")
    description: str = Field(..., description="规则检测目标与业务背景说明")
    enabled: bool = Field(default=True, description="规则是否启用")
    
    # 触发条件
    triggers: List[Trigger] = Field(..., description="触发条件列表")
    
    # 级联检查
    cascade_checks: List[CascadeCheck] = Field(default_factory=list, description="级联检查配置")
    
    # 违规响应
    violation_response: ViolationResponse = Field(..., description="违规响应配置")
    
    # 元数据
    metadata: RuleMetadata = Field(default_factory=RuleMetadata, description="规则元数据")
    
    @field_validator('rule_id')
    @classmethod
    def validate_rule_id(cls, v: str) -> str:
        """验证规则ID格式"""
        if not v or '-' not in v:
            raise ValueError("规则ID必须包含连字符，格式：{分类}-{场景}-{序号}")
        return v


class RuleSet(BaseModel):
    """规则集"""
    name: str = Field(..., description="规则集名称")
    description: str = Field(..., description="规则集描述")
    version: str = Field(default="1.0.0", description="规则集版本")
    rules: List[Rule] = Field(default_factory=list, description="规则列表")
    
    def get_enabled_rules(self) -> List[Rule]:
        """获取启用的规则"""
        return [r for r in self.rules if r.enabled]
    
    def get_rules_by_category(self, category: Category) -> List[Rule]:
        """按分类获取规则"""
        return [r for r in self.rules if r.category == category and r.enabled]
    
    def get_rules_by_severity(self, severity: Severity) -> List[Rule]:
        """按风险等级获取规则"""
        return [r for r in self.rules if r.severity == severity and r.enabled]
