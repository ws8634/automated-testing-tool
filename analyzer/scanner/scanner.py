"""
项目扫描器，用于扫描本地项目目录并识别文件结构
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Set


class ProjectScanner:
    """
    项目扫描器，负责扫描本地项目目录，识别项目类型和文件结构
    """
    
    SUPPORTED_EXTENSIONS = {
        'python': {'.py'},
        'javascript': {'.js', '.jsx'},
        'typescript': {'.ts', '.tsx'}
    }
    
    PROJECT_MARKERS = {
        'python': ['requirements.txt', 'setup.py', 'pyproject.toml', 'Pipfile'],
        'javascript': ['package.json', 'npm-shrinkwrap.json', 'yarn.lock'],
        'typescript': ['tsconfig.json', 'package.json']
    }
    
    def __init__(self, project_path: str):
        """
        初始化扫描器
        
        Args:
            project_path: 项目根目录路径
        """
        self.project_path = Path(project_path)
        if not self.project_path.exists():
            raise ValueError(f"项目路径不存在: {project_path}")
        self.files: List[Dict[str, Any]] = []
        self.project_type: str = None
    
    def scan(self) -> Dict[str, Any]:
        """
        执行项目扫描
        
        Returns:
            包含项目信息的字典
        """
        self._detect_project_type()
        self._collect_files()
        return self._build_result()
    
    def _detect_project_type(self) -> None:
        """
        检测项目类型
        """
        for lang, markers in self.PROJECT_MARKERS.items():
            for marker in markers:
                if (self.project_path / marker).exists():
                    self.project_type = lang
                    break
            if self.project_type:
                break
        
        if not self.project_type:
            self.project_type = 'unknown'
    
    def _collect_files(self) -> None:
        """
        收集项目文件
        """
        for root, dirs, files in os.walk(self.project_path):
            dirs[:] = [d for d in dirs if not self._is_excluded_dir(d)]
            
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(self.project_path)
                ext = file_path.suffix.lower()
                
                file_type = self._get_file_type(ext)
                if file_type:
                    self.files.append({
                        'path': str(rel_path),
                        'abs_path': str(file_path),
                        'type': file_type,
                        'size': file_path.stat().st_size
                    })
    
    def _is_excluded_dir(self, dir_name: str) -> bool:
        """
        检查是否为需要排除的目录
        
        Args:
            dir_name: 目录名称
            
        Returns:
            是否需要排除
        """
        excluded = {'.git', '.venv', 'venv', 'node_modules', '__pycache__', '.pytest_cache', 'dist', 'build'}
        return dir_name in excluded or dir_name.startswith('.')
    
    def _get_file_type(self, ext: str) -> str:
        """
        根据文件扩展名获取文件类型
        
        Args:
            ext: 文件扩展名
            
        Returns:
            文件类型字符串
        """
        for lang, exts in self.SUPPORTED_EXTENSIONS.items():
            if ext in exts:
                return lang
        return 'other'
    
    def _build_result(self) -> Dict[str, Any]:
        """
        构建扫描结果
        
        Returns:
            扫描结果字典
        """
        result = {
            'project_path': str(self.project_path),
            'project_type': self.project_type,
            'file_count': len(self.files),
            'files_by_type': {},
            'files': self.files
        }
        
        for file in self.files:
            ftype = file['type']
            if ftype not in result['files_by_type']:
                result['files_by_type'][ftype] = 0
            result['files_by_type'][ftype] += 1
        
        return result
    
    def get_python_files(self) -> List[Dict[str, Any]]:
        """
        获取所有Python文件
        
        Returns:
            Python文件列表
        """
        return [f for f in self.files if f['type'] == 'python']
    
    def get_js_files(self) -> List[Dict[str, Any]]:
        """
        获取所有JavaScript文件
        
        Returns:
            JavaScript文件列表
        """
        return [f for f in self.files if f['type'] == 'javascript']
    
    def get_ts_files(self) -> List[Dict[str, Any]]:
        """
        获取所有TypeScript文件
        
        Returns:
            TypeScript文件列表
        """
        return [f for f in self.files if f['type'] == 'typescript']
