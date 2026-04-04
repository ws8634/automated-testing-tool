"""
扫描相关数据模型

作者: Claude 3.5 Sonnet (Anthropic)
版本: 0.1.0
创建时间: 2026-03-14

功能目标:
    - 定义扫描结果的数据模型
    - 支持代码片段、违规项、扫描结果的表示
    - 提供扫描统计和查询方法

对应需求:
    1. 审核结果处理 - 报告生成所需数据结构
    2. 多源代码解析 - 支持不同来源的代码片段
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """代码来源类型"""
    GIT_DIFF = "git_diff"
    GIT_COMMIT = "git_commit"
    IDE_SNIPPET = "ide_snippet"
    FILE = "file"
    CONFIG = "config"


class CodeSnippet(BaseModel):
    """代码片段"""
    content: str = Field(..., description="代码内容")
    language: str = Field(..., description="编程语言")
    file_path: Optional[str] = Field(None, description="文件路径")
    line_start: int = Field(default=1, description="起始行号")
    line_end: int = Field(default=1, description="结束行号")
    source_type: SourceType = Field(..., description="代码来源类型")
    
    def get_line_content(self, line_num: int) -> str:
        """获取指定行的内容"""
        lines = self.content.split('\n')
        idx = line_num - self.line_start
        if 0 <= idx < len(lines):
            return lines[idx]
        return ""


class MatchLocation(BaseModel):
    """匹配位置信息"""
    line_number: int = Field(..., description="行号")
    column_start: int = Field(..., description="起始列")
    column_end: int = Field(..., description="结束列")
    matched_text: str = Field(..., description="匹配的文本")


class CascadeResult(BaseModel):
    """级联检查结果"""
    check_name: str = Field(..., description="检查名称")
    passed: bool = Field(..., description="是否通过")
    message: str = Field(..., description="检查结果消息")
    details: Dict[str, Any] = Field(default_factory=dict, description="详细检查结果")


class Violation(BaseModel):
    """违规项"""
    rule_id: str = Field(..., description="规则ID")
    rule_name: str = Field(..., description="规则名称")
    severity: str = Field(..., description="风险等级")
    category: str = Field(..., description="规则分类")
    message: str = Field(..., description="违规消息")
    file_path: Optional[str] = Field(None, description="文件路径")
    location: MatchLocation = Field(..., description="匹配位置")
    matched_content: str = Field(..., description="匹配的代码内容")
    suggested_fix: Optional[str] = Field(None, description="修复建议")
    cascade_results: List[CascadeResult] = Field(default_factory=list, description="级联检查结果")
    require_approval: Optional[str] = Field(None, description="需审批角色")
    docs_link: Optional[str] = Field(None, description="文档链接")
    
    def is_blocking(self) -> bool:
        """是否阻断性违规"""
        return self.severity in ["fatal", "error"]


class ScanSummary(BaseModel):
    """扫描摘要"""
    total_files: int = Field(default=0, description="扫描文件总数")
    total_lines: int = Field(default=0, description="扫描代码行数")
    fatal_count: int = Field(default=0, description="Fatal级别违规数")
    error_count: int = Field(default=0, description="Error级别违规数")
    warning_count: int = Field(default=0, description="Warning级别违规数")
    info_count: int = Field(default=0, description="Info级别违规数")
    
    @property
    def total_violations(self) -> int:
        """违规总数"""
        return self.fatal_count + self.error_count + self.warning_count + self.info_count
    
    @property
    def blocking_violations(self) -> int:
        """阻断性违规数"""
        return self.fatal_count + self.error_count


class ScanResult(BaseModel):
    """扫描结果"""
    scan_id: str = Field(..., description="扫描ID")
    start_time: datetime = Field(..., description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    source_type: SourceType = Field(..., description="代码来源类型")
    source_info: Dict[str, Any] = Field(default_factory=dict, description="来源详细信息")
    violations: List[Violation] = Field(default_factory=list, description="违规列表")
    summary: ScanSummary = Field(default_factory=ScanSummary, description="扫描摘要")
    
    def add_violation(self, violation: Violation) -> None:
        """添加违规项"""
        self.violations.append(violation)
        # 更新摘要
        if violation.severity == "fatal":
            self.summary.fatal_count += 1
        elif violation.severity == "error":
            self.summary.error_count += 1
        elif violation.severity == "warning":
            self.summary.warning_count += 1
        else:
            self.summary.info_count += 1
    
    def get_violations_by_severity(self, severity: str) -> List[Violation]:
        """按风险等级获取违规项"""
        return [v for v in self.violations if v.severity == severity]
    
    def get_violations_by_category(self, category: str) -> List[Violation]:
        """按分类获取违规项"""
        return [v for v in self.violations if v.category == category]
    
    def has_blocking_violations(self) -> bool:
        """是否有阻断性违规"""
        return self.summary.blocking_violations > 0
    
    def finalize(self) -> None:
        """完成扫描，设置结束时间"""
        self.end_time = datetime.now()
