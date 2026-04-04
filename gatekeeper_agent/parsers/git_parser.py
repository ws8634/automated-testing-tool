"""
Git 代码解析器
支持解析 Git Diff、Staged 变更、Commit 等
"""

import os
import re
from typing import List, Optional, Dict, Any
from pathlib import Path

try:
    import git
    from git import Repo, Commit
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False

from gatekeeper_agent.models.scan import CodeSnippet, SourceType
from gatekeeper_agent.utils.logger import get_logger

logger = get_logger(__name__)


class GitParser:
    """Git 代码解析器"""
    
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
        '.dockerfile': 'dockerfile',
        'dockerfile': 'dockerfile',
        '.tf': 'terraform',
        '.hcl': 'hcl',
    }
    
    def __init__(self):
        if not GIT_AVAILABLE:
            logger.warning("GitPython 未安装，Git 功能将不可用")
    
    def _get_language(self, file_path: str) -> str:
        """根据文件路径获取编程语言"""
        path = Path(file_path)
        ext = path.suffix.lower()
        
        # 检查 Dockerfile（无扩展名）
        if path.name.lower() == 'dockerfile':
            return 'dockerfile'
        
        return self.EXTENSION_LANGUAGE_MAP.get(ext, 'unknown')
    
    def _get_repo(self, repo_path: Optional[str] = None) -> Optional[Any]:
        """获取 Git 仓库对象"""
        if not GIT_AVAILABLE:
            return None
        
        try:
            path = repo_path or os.getcwd()
            return Repo(path, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            logger.error(f"无效的 Git 仓库: {repo_path or os.getcwd()}")
            return None
        except Exception as e:
            logger.error(f"获取 Git 仓库失败: {e}")
            return None
    
    def parse_diff(
        self,
        repo_path: Optional[str] = None,
        target: str = "HEAD",
        source: Optional[str] = None
    ) -> List[CodeSnippet]:
        """
        解析 Git Diff
        
        Args:
            repo_path: Git 仓库路径
            target: 目标分支或提交
            source: 源分支或提交，None 表示工作区
            
        Returns:
            List[CodeSnippet]: 代码片段列表
        """
        repo = self._get_repo(repo_path)
        if not repo:
            return []
        
        try:
            # 获取 diff
            if source:
                # 比较两个提交/分支
                diff_index = repo.commit(source).diff(target)
            else:
                # 比较工作区与 target
                diff_index = repo.head.commit.diff(target)
            
            return self._parse_diff_index(repo, diff_index)
            
        except Exception as e:
            logger.error(f"解析 Git Diff 失败: {e}")
            return []
    
    def parse_staged(self, repo_path: Optional[str] = None) -> List[CodeSnippet]:
        """
        解析暂存区（Staged）的变更
        
        Args:
            repo_path: Git 仓库路径
            
        Returns:
            List[CodeSnippet]: 代码片段列表
        """
        repo = self._get_repo(repo_path)
        if not repo:
            return []
        
        try:
            # 获取暂存区的 diff
            diff_index = repo.index.diff(repo.head.commit)
            return self._parse_diff_index(repo, diff_index)
            
        except Exception as e:
            logger.error(f"解析暂存区失败: {e}")
            return []
    
    def parse_commit(
        self,
        commit_hash: str,
        repo_path: Optional[str] = None
    ) -> List[CodeSnippet]:
        """
        解析指定提交的变更
        
        Args:
            commit_hash: 提交哈希
            repo_path: Git 仓库路径
            
        Returns:
            List[CodeSnippet]: 代码片段列表
        """
        repo = self._get_repo(repo_path)
        if not repo:
            return []
        
        try:
            commit = repo.commit(commit_hash)
            
            # 获取父提交
            if not commit.parents:
                # 初始提交，比较空树
                diff_index = commit.diff(git.Tree.NULL)
            else:
                # 与父提交比较
                parent = commit.parents[0]
                diff_index = parent.diff(commit)
            
            return self._parse_diff_index(repo, diff_index)
            
        except Exception as e:
            logger.error(f"解析提交失败: {e}")
            return []
    
    def _parse_diff_index(self, repo: Any, diff_index: Any) -> List[CodeSnippet]:
        """解析 diff index 为代码片段"""
        snippets = []
        
        for diff_item in diff_index:
            # 跳过删除的文件和二进制文件
            if diff_item.deleted_file or diff_item.is_binary:
                continue
            
            file_path = diff_item.b_path or diff_item.a_path
            
            try:
                # 获取变更的内容
                if diff_item.b_blob:
                    content = diff_item.b_blob.data_stream.read().decode('utf-8', errors='ignore')
                else:
                    # 工作区文件
                    full_path = os.path.join(repo.working_dir, file_path)
                    if os.path.exists(full_path):
                        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                    else:
                        continue
                
                # 获取变更的行范围（简化处理，实际应该解析 diff 内容）
                diff_text = diff_item.diff.decode('utf-8', errors='ignore') if diff_item.diff else ""
                line_ranges = self._extract_changed_lines(diff_text)
                
                if line_ranges:
                    # 为每个变更范围创建代码片段
                    for start, end in line_ranges:
                        lines = content.split('\n')
                        # 添加上下文（前后3行）
                        context_start = max(0, start - 4)
                        context_end = min(len(lines), end + 3)
                        
                        snippet_content = '\n'.join(lines[context_start:context_end])
                        
                        snippet = CodeSnippet(
                            content=snippet_content,
                            language=self._get_language(file_path),
                            file_path=file_path,
                            line_start=context_start + 1,
                            line_end=context_end,
                            source_type=SourceType.GIT_DIFF
                        )
                        snippets.append(snippet)
                else:
                    # 如果没有解析到行范围，使用整个文件
                    snippet = CodeSnippet(
                        content=content,
                        language=self._get_language(file_path),
                        file_path=file_path,
                        line_start=1,
                        line_end=len(content.split('\n')),
                        source_type=SourceType.GIT_DIFF
                    )
                    snippets.append(snippet)
                    
            except Exception as e:
                logger.warning(f"解析文件失败 {file_path}: {e}")
                continue
        
        return snippets
    
    def _extract_changed_lines(self, diff_text: str) -> List[tuple]:
        """
        从 diff 文本中提取变更的行范围
        
        Returns:
            List[tuple]: (start_line, end_line) 列表
        """
        ranges = []
        
        # 解析 @@ 行，例如：@@ -1,5 +1,7 @@
        pattern = r'@@[\s\-\+,\d]+\s\+(\d+)(?:,(\d+))?\s@@'
        
        for match in re.finditer(pattern, diff_text):
            start = int(match.group(1))
            count = int(match.group(2)) if match.group(2) else 1
            end = start + count - 1
            ranges.append((start, end))
        
        return ranges
    
    def get_changed_files(
        self,
        repo_path: Optional[str] = None,
        target: str = "HEAD",
        source: Optional[str] = None
    ) -> List[str]:
        """
        获取变更的文件列表
        
        Args:
            repo_path: Git 仓库路径
            target: 目标分支或提交
            source: 源分支或提交
            
        Returns:
            List[str]: 变更的文件路径列表
        """
        repo = self._get_repo(repo_path)
        if not repo:
            return []
        
        try:
            if source:
                diff_index = repo.commit(source).diff(target)
            else:
                diff_index = repo.head.commit.diff(target)
            
            files = []
            for diff_item in diff_index:
                if not diff_item.deleted_file:
                    files.append(diff_item.b_path or diff_item.a_path)
            
            return files
            
        except Exception as e:
            logger.error(f"获取变更文件失败: {e}")
            return []
