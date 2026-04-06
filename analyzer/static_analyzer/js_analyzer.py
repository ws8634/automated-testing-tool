"""
JavaScript/TypeScript静态分析器，基于正则和AST分析JS/TS代码结构
"""
import re
import os
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict


class JavaScriptStaticAnalyzer:
    """
    JavaScript/TypeScript静态分析器，负责解析JS/TS代码的结构和依赖关系
    """
    
    def __init__(self, project_path: str):
        """
        初始化JavaScript静态分析器
        
        Args:
            project_path: 项目根目录路径
        """
        self.project_path = Path(project_path)
        self.classes: Dict[str, Dict[str, Any]] = {}
        self.functions: Dict[str, Dict[str, Any]] = {}
        self.calls: List[Dict[str, Any]] = []
        self.imports: List[Dict[str, Any]] = []
        self.current_file: str = None
    
    def analyze(self, js_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析JavaScript/TypeScript文件
        
        Args:
            js_files: JS/TS文件列表
            
        Returns:
            分析结果字典
        """
        for file_info in js_files:
            self._analyze_file(file_info['abs_path'], file_info['path'])
        
        return self._build_result()
    
    def _analyze_file(self, abs_path: str, rel_path: str) -> None:
        """
        分析单个JS/TS文件
        
        Args:
            abs_path: 文件绝对路径
            rel_path: 文件相对路径
        """
        self.current_file = rel_path
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                source = f.read()
            self._analyze_source(source)
        except Exception as e:
            print(f"分析文件 {abs_path} 时出错: {e}")
    
    def _analyze_source(self, source: str) -> None:
        """
        分析源代码
        
        Args:
            source: 源代码字符串
        """
        self._extract_imports(source)
        self._extract_classes(source)
        self._extract_functions(source)
        self._extract_calls(source)
    
    def _extract_imports(self, source: str) -> None:
        """
        提取import语句
        
        Args:
            source: 源代码字符串
        """
        import_patterns = [
            r'import\s+.*?from\s+[\'"]([^\'"]+)[\'"]',
            r'require\s*\(\s*[\'"]([^\'"]+)[\'"]\s*\)'
        ]
        
        for pattern in import_patterns:
            for match in re.finditer(pattern, source):
                self.imports.append({
                    'file': self.current_file,
                    'module': match.group(1)
                })
    
    def _extract_classes(self, source: str) -> None:
        """
        提取类定义
        
        Args:
            source: 源代码字符串
        """
        class_pattern = r'class\s+(\w+)\s*(?:extends\s+(\w+))?'
        
        for match in re.finditer(class_pattern, source):
            class_name = match.group(1)
            base_class = match.group(2) if match.group(2) else None
            
            self.classes[class_name] = {
                'name': class_name,
                'file': self.current_file,
                'base': base_class,
                'methods': []
            }
            
            class_body = self._extract_class_body(source, match.end())
            self._extract_methods(class_body, class_name)
    
    def _extract_class_body(self, source: str, start_pos: int) -> str:
        """
        提取类体
        
        Args:
            source: 源代码字符串
            start_pos: 起始位置
            
        Returns:
            类体字符串
        """
        brace_count = 0
        body_start = -1
        
        for i in range(start_pos, len(source)):
            if source[i] == '{':
                if body_start == -1:
                    body_start = i
                brace_count += 1
            elif source[i] == '}':
                brace_count -= 1
                if brace_count == 0 and body_start != -1:
                    return source[body_start:i+1]
        
        return ''
    
    def _extract_methods(self, class_body: str, class_name: str) -> None:
        """
        提取类方法
        
        Args:
            class_body: 类体字符串
            class_name: 类名
        """
        method_pattern = r'(?:async\s+)?(\w+)\s*\([^)]*\)\s*{'
        
        for match in re.finditer(method_pattern, class_body):
            method_name = match.group(1)
            if method_name not in ['if', 'for', 'while', 'switch', 'try', 'catch']:
                if class_name in self.classes:
                    self.classes[class_name]['methods'].append(method_name)
    
    def _extract_functions(self, source: str) -> None:
        """
        提取函数定义
        
        Args:
            source: 源代码字符串
        """
        func_patterns = [
            r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(',
            r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)|function)\s*',
            r'(?:export\s+)?(?:async\s+)?(\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>'
        ]
        
        for pattern in func_patterns:
            for match in re.finditer(pattern, source):
                func_name = match.group(1)
                if func_name and func_name not in self.functions:
                    self.functions[func_name] = {
                        'name': func_name,
                        'file': self.current_file,
                        'is_method': False
                    }
    
    def _extract_calls(self, source: str) -> None:
        """
        提取函数调用
        
        Args:
            source: 源代码字符串
        """
        call_pattern = r'(\w+)\s*\('
        
        for match in re.finditer(call_pattern, source):
            callee = match.group(1)
            if callee not in ['if', 'for', 'while', 'switch', 'try', 'catch', 'return', 'new']:
                self.calls.append({
                    'file': self.current_file,
                    'callee': callee
                })
    
    def _build_result(self) -> Dict[str, Any]:
        """
        构建分析结果
        
        Returns:
            分析结果字典
        """
        return {
            'classes': self.classes,
            'functions': self.functions,
            'calls': self.calls,
            'imports': self.imports,
            'class_count': len(self.classes),
            'function_count': len(self.functions),
            'call_count': len(self.calls)
        }
