"""
文件解析器
支持解析单个文件和目录
"""

import os
import fnmatch
from typing import List, Optional
from pathlib import Path

from gatekeeper_agent.models.scan import CodeSnippet, SourceType
from gatekeeper_agent.utils.logger import get_logger

logger = get_logger(__name__)


class FileParser:
    """文件解析器"""
    
    # 默认排除的模式
    DEFAULT_EXCLUDE_PATTERNS = [
        '.git',
        '.svn',
        '.hg',
        'node_modules',
        '__pycache__',
        '*.pyc',
        '*.pyo',
        '.pytest_cache',
        '.mypy_cache',
        '.tox',
        'venv',
        '.venv',
        'env',
        '.env',
        'dist',
        'build',
        '*.egg-info',
        '.idea',
        '.vscode',
        '*.min.js',
        '*.min.css',
        '*.map',
    ]
    
    # 文件扩展名到语言的映射
    EXTENSION_LANGUAGE_MAP = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.go': 'go',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.sh': 'shell',
        '.bash': 'shell',
        '.zsh': 'shell',
        '.sql': 'sql',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.json': 'json',
        '.xml': 'xml',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        '.md': 'markdown',
        '.tf': 'terraform',
        '.hcl': 'hcl',
    }
    
    def __init__(self):
        self.exclude_patterns = self.DEFAULT_EXCLUDE_PATTERNS.copy()
    
    def _get_language(self, file_path: str) -> str:
        """根据文件路径获取编程语言"""
        path = Path(file_path)
        ext = path.suffix.lower()
        
        # 检查 Dockerfile
        if path.name.lower() == 'dockerfile':
            return 'dockerfile'
        
        # 检查 Makefile
        if path.name.lower() == 'makefile':
            return 'makefile'
        
        return self.EXTENSION_LANGUAGE_MAP.get(ext, 'unknown')
    
    def _should_exclude(self, path: str, patterns: List[str]) -> bool:
        """检查路径是否应该被排除"""
        path_parts = Path(path).parts
        
        for pattern in patterns:
            # 检查路径的任何部分是否匹配
            for part in path_parts:
                if fnmatch.fnmatch(part, pattern):
                    return True
            # 检查完整路径是否匹配
            if fnmatch.fnmatch(path, pattern):
                return True
            if fnmatch.fnmatch(os.path.basename(path), pattern):
                return True
        
        return False
    
    def parse_file(self, file_path: str) -> Optional[CodeSnippet]:
        """
        解析单个文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            Optional[CodeSnippet]: 代码片段，如果解析失败返回 None
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.warning(f"文件不存在: {file_path}")
            return None
        
        if not path.is_file():
            logger.warning(f"不是文件: {file_path}")
            return None
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            
            return CodeSnippet(
                content=content,
                language=self._get_language(file_path),
                file_path=str(path.absolute()),
                line_start=1,
                line_end=len(lines),
                source_type=SourceType.FILE
            )
            
        except Exception as e:
            logger.error(f"解析文件失败 {file_path}: {e}")
            return None
    
    def parse_directory(
        self,
        dir_path: str,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> List[CodeSnippet]:
        """
        解析目录中的所有文件
        
        Args:
            dir_path: 目录路径
            include_patterns: 包含的文件模式列表
            exclude_patterns: 排除的文件模式列表（在默认排除模式基础上）
            
        Returns:
            List[CodeSnippet]: 代码片段列表
        """
        path = Path(dir_path)
        
        if not path.exists():
            logger.warning(f"目录不存在: {dir_path}")
            return []
        
        if not path.is_dir():
            logger.warning(f"不是目录: {dir_path}")
            return []
        
        # 合并排除模式
        all_exclude_patterns = self.exclude_patterns.copy()
        if exclude_patterns:
            all_exclude_patterns.extend(exclude_patterns)
        
        snippets = []
        
        for root, dirs, files in os.walk(path):
            # 过滤目录
            dirs[:] = [
                d for d in dirs 
                if not self._should_exclude(os.path.join(root, d), all_exclude_patterns)
            ]
            
            for file_name in files:
                file_path = os.path.join(root, file_name)
                
                # 检查是否应该排除
                if self._should_exclude(file_path, all_exclude_patterns):
                    continue
                
                # 检查是否匹配包含模式
                if include_patterns:
                    if not any(fnmatch.fnmatch(file_name, p) for p in include_patterns):
                        if not any(fnmatch.fnmatch(file_path, p) for p in include_patterns):
                            continue
                
                # 解析文件
                snippet = self.parse_file(file_path)
                if snippet:
                    snippets.append(snippet)
        
        logger.info(f"从目录 {dir_path} 解析了 {len(snippets)} 个文件")
        return snippets
    
    def parse_files(self, file_paths: List[str]) -> List[CodeSnippet]:
        """
        解析多个文件
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            List[CodeSnippet]: 代码片段列表
        """
        snippets = []
        
        for file_path in file_paths:
            snippet = self.parse_file(file_path)
            if snippet:
                snippets.append(snippet)
        
        return snippets
    
    def get_supported_extensions(self) -> List[str]:
        """获取支持的文件扩展名列表"""
        return list(self.EXTENSION_LANGUAGE_MAP.keys())
    
    def is_supported_file(self, file_path: str) -> bool:
        """检查文件是否受支持"""
        path = Path(file_path)
        
        # 特殊文件
        if path.name.lower() in ['dockerfile', 'makefile']:
            return True
        
        return path.suffix.lower() in self.EXTENSION_LANGUAGE_MAP
