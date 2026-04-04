"""
代码扫描器 - 统一入口

作者: Claude 3.5 Sonnet (Anthropic)
版本: 0.1.0
创建时间: 2025-03-13

功能目标:
    - 提供统一的代码审核入口
    - 支持多种代码来源：Git Diff、文件、IDE代码片段
    - 封装规则引擎，简化调用

对应需求:
    1. 多源代码解析 - Git/IDE/文件
    2. 代码扫描统一接口

处理逻辑:
    1. 根据来源类型调用对应的解析器
    2. 使用规则引擎执行扫描
    3. 返回标准化的扫描结果
"""

import os
from typing import Any, Dict, List, Optional
from pathlib import Path

from gatekeeper_agent.models.rule import RuleSet
from gatekeeper_agent.models.scan import CodeSnippet, SourceType, ScanResult
from gatekeeper_agent.core.engine import RuleEngine
from gatekeeper_agent.parsers.git_parser import GitParser
from gatekeeper_agent.parsers.file_parser import FileParser
from gatekeeper_agent.utils.logger import get_logger

logger = get_logger(__name__)


class CodeScanner:
    """
    代码扫描器 - 统一的代码审核入口
    支持多种代码来源：Git Diff、文件、IDE代码片段
    """
    
    def __init__(self, rule_set: RuleSet):
        """
        初始化代码扫描器
        
        Args:
            rule_set: 规则集对象
        """
        self.rule_set = rule_set
        self.engine = RuleEngine(rule_set)
        self.git_parser = GitParser()
        self.file_parser = FileParser()
    
    def scan_git_diff(
        self, 
        repo_path: Optional[str] = None,
        target: str = "HEAD",
        source: Optional[str] = None
    ) -> ScanResult:
        """
        扫描 Git Diff
        
        Args:
            repo_path: Git仓库路径，默认为当前目录
            target: 目标分支或提交
            source: 源分支或提交，为None时比较工作区与target
            
        Returns:
            ScanResult: 扫描结果
        """
        logger.info(f"扫描 Git Diff: {source or 'WORKING'} -> {target}")
        
        # 解析 Git Diff
        code_snippets = self.git_parser.parse_diff(
            repo_path=repo_path,
            target=target,
            source=source
        )
        
        if not code_snippets:
            logger.info("没有检测到代码变更")
            return self._create_empty_result(SourceType.GIT_DIFF)
        
        # 批量扫描
        result = self.engine.scan_batch(code_snippets)
        result.source_type = SourceType.GIT_DIFF
        result.source_info = {
            "repo_path": repo_path or os.getcwd(),
            "target": target,
            "source": source or "WORKING"
        }
        
        return result
    
    def scan_staged(self, repo_path: Optional[str] = None) -> ScanResult:
        """
        扫描暂存区（Git Staged）的变更
        
        Args:
            repo_path: Git仓库路径
            
        Returns:
            ScanResult: 扫描结果
        """
        logger.info("扫描暂存区变更")
        
        code_snippets = self.git_parser.parse_staged(repo_path)
        
        if not code_snippets:
            logger.info("暂存区没有代码变更")
            return self._create_empty_result(SourceType.GIT_DIFF)
        
        result = self.engine.scan_batch(code_snippets)
        result.source_type = SourceType.GIT_DIFF
        result.source_info = {
            "repo_path": repo_path or os.getcwd(),
            "type": "staged"
        }
        
        return result
    
    def scan_file(self, file_path: str) -> ScanResult:
        """
        扫描单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            ScanResult: 扫描结果
        """
        logger.info(f"扫描文件: {file_path}")
        
        code_snippet = self.file_parser.parse_file(file_path)
        
        if not code_snippet:
            logger.warning(f"无法解析文件: {file_path}")
            return self._create_empty_result(SourceType.FILE)
        
        result = self.engine.scan(code_snippet)
        return result
    
    def scan_directory(
        self, 
        dir_path: str, 
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> ScanResult:
        """
        扫描目录
        
        Args:
            dir_path: 目录路径
            include_patterns: 包含的文件模式列表
            exclude_patterns: 排除的文件模式列表
            
        Returns:
            ScanResult: 扫描结果
        """
        logger.info(f"扫描目录: {dir_path}")
        
        code_snippets = self.file_parser.parse_directory(
            dir_path=dir_path,
            include_patterns=include_patterns,
            exclude_patterns=exclude_patterns
        )
        
        if not code_snippets:
            logger.info("目录中没有可扫描的文件")
            return self._create_empty_result(SourceType.FILE)
        
        result = self.engine.scan_batch(code_snippets)
        result.source_type = SourceType.FILE
        result.source_info = {
            "directory": dir_path,
            "file_count": len(code_snippets)
        }
        
        return result
    
    def scan_snippet(
        self, 
        content: str, 
        language: str,
        file_path: Optional[str] = None,
        is_ai_generated: bool = False
    ) -> ScanResult:
        """
        扫描代码片段（IDE集成用）
        
        Args:
            content: 代码内容
            language: 编程语言
            file_path: 文件路径（可选）
            is_ai_generated: 是否为AI生成的代码
            
        Returns:
            ScanResult: 扫描结果
        """
        logger.info(f"扫描代码片段: {language}")
        
        lines = content.split('\n')
        code_snippet = CodeSnippet(
            content=content,
            language=language,
            file_path=file_path,
            line_start=1,
            line_end=len(lines),
            source_type=SourceType.IDE_SNIPPET
        )
        
        # 标记AI生成代码
        if is_ai_generated:
            code_snippet.is_ai_generated = True
        
        result = self.engine.scan(code_snippet)
        return result
    
    def scan_commit(
        self,
        commit_hash: str,
        repo_path: Optional[str] = None
    ) -> ScanResult:
        """
        扫描指定提交的变更
        
        Args:
            commit_hash: 提交哈希
            repo_path: Git仓库路径
            
        Returns:
            ScanResult: 扫描结果
        """
        logger.info(f"扫描提交: {commit_hash}")
        
        code_snippets = self.git_parser.parse_commit(
            commit_hash=commit_hash,
            repo_path=repo_path
        )
        
        if not code_snippets:
            logger.info("提交中没有代码变更")
            return self._create_empty_result(SourceType.GIT_COMMIT)
        
        result = self.engine.scan_batch(code_snippets)
        result.source_type = SourceType.GIT_COMMIT
        result.source_info = {
            "commit_hash": commit_hash,
            "repo_path": repo_path or os.getcwd()
        }
        
        return result
    
    def _create_empty_result(self, source_type: SourceType) -> ScanResult:
        """创建空扫描结果"""
        from datetime import datetime
        import uuid
        
        return ScanResult(
            scan_id=str(uuid.uuid4())[:8],
            start_time=datetime.now(),
            end_time=datetime.now(),
            source_type=source_type,
            source_info={},
            violations=[],
        )
