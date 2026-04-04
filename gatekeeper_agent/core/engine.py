"""
规则引擎核心模块 (Rule Engine Core Module)

作者: GatekeeperAgent (AI Assistant, Claude 3.5 Sonnet)
版本: 0.1.0
创建时间: 2026-03-14
最后更新: 2026-03-14

功能目标:
    - 实现静态代码审核的核心逻辑
    - 支持正则表达式规则匹配
    - 实现级联检查(Cascade Check)机制
    - 提供单文件和批量扫描能力

对应需求:
    1. 标准化规则引擎 - 规则解析和执行
    2. 级联检查能力 - 高危操作的关联校验
    3. 多检测模式 - 正则匹配、AST解析、LLM混合检测

处理逻辑:
    1. 初始化时预编译所有规则的正则表达式(提升性能)
    2. 根据代码片段的语言、文件类型筛选适用规则
    3. 对每条约规执行正则匹配
    4. 匹配成功后执行级联检查(验证must_contain/must_not_contain)
    5. 根据级联检查结果调整风险等级
    6. 生成详细的违规报告
"""

import re
import uuid
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from gatekeeper_agent.models.rule import Rule, RuleSet, Severity, Category, CascadeCheck
from gatekeeper_agent.models.scan import (
    CodeSnippet, ScanResult, Violation, MatchLocation, 
    CascadeResult, SourceType, ScanSummary
)
from gatekeeper_agent.utils.logger import get_logger

logger = get_logger(__name__)


class RuleEngine:
    """
    规则引擎 - 核心审核逻辑
    
    职责:
        - 管理和执行审核规则
        - 编译和缓存正则表达式
        - 执行级联检查
        - 生成扫描结果
    """
    
    def __init__(self, rule_set: RuleSet):
        """
        初始化规则引擎
        
        Args:
            rule_set: 规则集对象，包含所有要执行的规则
        """
        self.rule_set = rule_set
        self._compiled_patterns: Dict[str, re.Pattern] = {}
        self._compile_patterns()
    
    def _compile_patterns(self) -> None:
        """
        预编译所有规则的正则表达式
        
        性能优化: 避免在扫描过程中重复编译正则表达式
        """
        for rule in self.rule_set.rules:
            for i, trigger in enumerate(rule.triggers):
                key = f"{rule.rule_id}_{i}"
                try:
                    self._compiled_patterns[key] = re.compile(
                        trigger.pattern, 
                        re.MULTILINE | re.IGNORECASE
                    )
                except re.error as e:
                    logger.error(f"规则 {rule.rule_id} 的正则表达式编译失败: {e}")
    
    def scan(self, code_snippet: CodeSnippet, context: Optional[Dict[str, Any]] = None) -> ScanResult:
        """
        扫描单个代码片段
        
        处理流程:
            1. 创建扫描结果对象
            2. 筛选适用于该代码片段的规则
            3. 逐条执行规则检查
            4. 汇总违规结果
        
        Args:
            code_snippet: 代码片段对象，包含内容、语言、文件路径等信息
            context: 额外上下文信息(如PRD文本、AI生成标记等)
            
        Returns:
            ScanResult: 扫描结果，包含所有发现的违规项
        """
        scan_id = str(uuid.uuid4())[:8]
        result = ScanResult(
            scan_id=scan_id,
            start_time=datetime.now(),
            source_type=code_snippet.source_type,
            source_info={
                "file_path": code_snippet.file_path,
                "language": code_snippet.language,
            }
        )
        
        # 更新摘要统计
        result.summary.total_files = 1
        result.summary.total_lines = code_snippet.line_end - code_snippet.line_start + 1
        
        # 获取适用于当前代码的规则(按语言和文件类型筛选)
        applicable_rules = self._get_applicable_rules(code_snippet)
        file_name = code_snippet.file_path or "未知文件"
        logger.info(f"[{scan_id}] 扫描文件: {file_name} (语言: {code_snippet.language}, 适用规则: {len(applicable_rules)}条)")
        
        # 执行规则检测
        seen_violations = set()  # 用于去重
        for rule in applicable_rules:
            violations = self._check_rule(rule, code_snippet, context)
            for violation in violations:
                # 创建唯一标识：规则ID + 文件路径 + 行号 + 匹配内容
                violation_key = (
                    violation.rule_id,
                    violation.file_path,
                    violation.location.line_number,
                    violation.matched_content
                )
                if violation_key not in seen_violations:
                    seen_violations.add(violation_key)
                    result.add_violation(violation)
        
        result.finalize()
        if result.summary.total_violations > 0:
            logger.warning(f"[{scan_id}] 文件 {file_name}: 发现 {result.summary.total_violations} 个违规项")
        else:
            logger.info(f"[{scan_id}] 文件 {file_name}: 未发现违规")
        
        return result
    
    def _get_applicable_rules(self, code_snippet: CodeSnippet) -> List[Rule]:
        """
        获取适用于当前代码片段的规则
        
        筛选逻辑:
            1. 只选择启用的规则
            2. AI专用规则只检查AI生成的代码
            3. 按编程语言筛选
            4. 按文件路径模式筛选
        
        Args:
            code_snippet: 代码片段
            
        Returns:
            List[Rule]: 适用的规则列表
        """
        applicable = []
        
        for rule in self.rule_set.get_enabled_rules():
            # 检查AI代码专用规则
            if rule.metadata.ai_code_only:
                is_ai_code = getattr(code_snippet, 'is_ai_generated', False)
                if not is_ai_code:
                    continue
            
            # 检查触发条件
            for trigger in rule.triggers:
                # 检查语言匹配
                if trigger.language and code_snippet.language not in trigger.language:
                    continue
                
                # 检查文件模式匹配
                if trigger.file_pattern and code_snippet.file_path:
                    if not any(
                        self._match_file_pattern(code_snippet.file_path, pattern)
                        for pattern in trigger.file_pattern
                    ):
                        continue
                
                applicable.append(rule)
                break
        
        return applicable
    
    def _match_file_pattern(self, file_path: str, pattern: str) -> bool:
        """
        匹配文件路径模式
        
        Args:
            file_path: 文件路径
            pattern: glob模式(如 "*.py", "src/**/*.js")
            
        Returns:
            bool: 是否匹配
        """
        import fnmatch
        return fnmatch.fnmatch(file_path, pattern)
    
    def _check_rule(
        self, 
        rule: Rule, 
        code_snippet: CodeSnippet,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Violation]:
        """
        检查单条规则
        
        处理流程:
            1. 执行正则表达式匹配
            2. 计算匹配位置的行号和列号
            3. 执行级联检查
            4. 根据级联结果调整风险等级
            5. 生成违规项对象
        
        Args:
            rule: 要检查的规则
            code_snippet: 代码片段
            context: 额外上下文
            
        Returns:
            List[Violation]: 发现的违规项列表
        """
        violations = []
        
        for trigger_idx, trigger in enumerate(rule.triggers):
            pattern_key = f"{rule.rule_id}_{trigger_idx}"
            compiled_pattern = self._compiled_patterns.get(pattern_key)
            
            if not compiled_pattern:
                continue
            
            # 执行正则匹配
            for match in compiled_pattern.finditer(code_snippet.content):
                # 计算行号(相对于代码片段的起始行)
                line_number = code_snippet.line_start + code_snippet.content[:match.start()].count('\n')
                
                # 获取匹配位置的列信息
                line_start_pos = code_snippet.content.rfind('\n', 0, match.start()) + 1
                line_end_pos = code_snippet.content.find('\n', match.end())
                if line_end_pos == -1:
                    line_end_pos = len(code_snippet.content)
                
                column_start = match.start() - line_start_pos + 1
                column_end = match.end() - line_start_pos + 1
                
                # 获取完整行内容
                full_line = code_snippet.content[line_start_pos:line_end_pos].strip()
                
                location = MatchLocation(
                    line_number=line_number,
                    column_start=column_start,
                    column_end=column_end,
                    matched_text=full_line
                )
                
                # 执行级联检查
                cascade_results = []
                final_severity = rule.severity.value
                
                for cascade_check in rule.cascade_checks:
                    cascade_result = self._run_cascade_check(
                        cascade_check, code_snippet, match, context
                    )
                    cascade_results.append(cascade_result)
                    
                    # 根据级联检查结果调整严重级别
                    if not cascade_result.passed:
                        if cascade_check.fail_action.value == "upgrade_severity":
                            if final_severity == "warning":
                                final_severity = "error"
                            elif final_severity == "error":
                                final_severity = "fatal"
                
                # 创建违规项
                message = rule.violation_response.message.format(
                    rule_id=rule.rule_id,
                    file_path=code_snippet.file_path or "unknown",
                    match_content=match.group(0)
                )
                
                violation = Violation(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    severity=final_severity,
                    category=rule.category.value,
                    message=message,
                    file_path=code_snippet.file_path,
                    location=location,
                    matched_content=match.group(0),
                    suggested_fix=rule.violation_response.suggested_fix,
                    cascade_results=cascade_results,
                    require_approval=rule.violation_response.require_approval,
                    docs_link=rule.violation_response.docs_link
                )
                
                violations.append(violation)
        
        return violations
    
    def _run_cascade_check(
        self,
        cascade_check: CascadeCheck,
        code_snippet: CodeSnippet,
        match: re.Match,
        context: Optional[Dict[str, Any]] = None
    ) -> CascadeResult:
        """
        执行级联检查
        
        级联检查逻辑:
            1. must_contain: 检查代码中必须存在的模式
            2. must_not_contain: 检查代码中禁止存在的模式
            3. ast_check: AST节点类型检查(待实现)
            4. llm_intent_check: LLM意图匹配校验(待实现)
        
        Args:
            cascade_check: 级联检查配置
            code_snippet: 代码片段
            match: 正则匹配结果
            context: 额外上下文
            
        Returns:
            CascadeResult: 级联检查结果
        """
        validation = cascade_check.validation
        details = {}
        
        # 检查 must_contain - 验证必需的安全措施是否存在
        for pattern in validation.must_contain:
            if not re.search(pattern, code_snippet.content, re.IGNORECASE):
                return CascadeResult(
                    check_name=cascade_check.name,
                    passed=False,
                    message=f"未找到必需的代码模式: {pattern}",
                    details={"missing_pattern": pattern}
                )
        
        # 检查 must_not_contain - 验证禁止的危险操作
        for pattern in validation.must_not_contain:
            if re.search(pattern, code_snippet.content, re.IGNORECASE):
                return CascadeResult(
                    check_name=cascade_check.name,
                    passed=False,
                    message=f"发现禁止的代码模式: {pattern}",
                    details={"forbidden_pattern": pattern}
                )
        
        # AST检查（简化实现，预留扩展接口）
        if validation.ast_check:
            # TODO: 实现AST检查，用于更精确的代码结构分析
            pass
        
        # LLM意图检查（简化实现，预留扩展接口）
        if validation.llm_intent_check:
            # TODO: 实现LLM意图检查，用于验证代码是否符合PRD需求
            pass
        
        return CascadeResult(
            check_name=cascade_check.name,
            passed=True,
            message="级联检查通过",
            details=details
        )
    
    def scan_batch(
        self, 
        code_snippets: List[CodeSnippet],
        context: Optional[Dict[str, Any]] = None
    ) -> ScanResult:
        """
        批量扫描多个代码片段
        
        Args:
            code_snippets: 代码片段列表
            context: 额外上下文信息
            
        Returns:
            ScanResult: 合并的扫描结果
        """
        scan_id = str(uuid.uuid4())[:8]
        result = ScanResult(
            scan_id=scan_id,
            start_time=datetime.now(),
            source_type=SourceType.FILE,
            source_info={"batch_size": len(code_snippets)}
        )
        
        for snippet in code_snippets:
            snippet_result = self.scan(snippet, context)
            for violation in snippet_result.violations:
                result.add_violation(violation)
            result.summary.total_files += 1
            result.summary.total_lines += snippet_result.summary.total_lines
        
        result.finalize()
        return result
