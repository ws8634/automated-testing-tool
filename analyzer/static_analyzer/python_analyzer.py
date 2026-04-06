"""
Python静态分析器，基于AST解析分析Python代码结构和依赖关系
"""
import ast
import os
from pathlib import Path
from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict


class PythonStaticAnalyzer:
    """
    Python静态分析器，负责解析Python代码的AST，识别类、方法、调用关系等
    """
    
    def __init__(self, project_path: str):
        """
        初始化Python静态分析器
        
        Args:
            project_path: 项目根目录路径
        """
        self.project_path = Path(project_path)
        self.classes: Dict[str, Dict[str, Any]] = {}
        self.functions: Dict[str, Dict[str, Any]] = {}
        self.calls: List[Dict[str, Any]] = []
        self.imports: List[Dict[str, Any]] = []
        self.current_file: str = None
        self._class_stack: List[str] = []
    
    def analyze(self, python_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析Python文件
        
        Args:
            python_files: Python文件列表
            
        Returns:
            分析结果字典
        """
        for file_info in python_files:
            self._analyze_file(file_info['abs_path'], file_info['path'])
        
        return self._build_result()
    
    def _analyze_file(self, abs_path: str, rel_path: str) -> None:
        """
        分析单个Python文件
        
        Args:
            abs_path: 文件绝对路径
            rel_path: 文件相对路径
        """
        self.current_file = rel_path
        try:
            with open(abs_path, 'r', encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=abs_path)
            self._visit_tree(tree)
        except Exception as e:
            print(f"分析文件 {abs_path} 时出错: {e}")
    
    def _visit_tree(self, tree: ast.AST) -> None:
        """
        遍历AST树
        
        Args:
            tree: AST节点
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self._process_import(node)
            elif isinstance(node, ast.ImportFrom):
                self._process_import_from(node)
            elif isinstance(node, ast.ClassDef):
                self._process_class(node)
            elif isinstance(node, ast.FunctionDef):
                self._process_function(node)
            elif isinstance(node, ast.AsyncFunctionDef):
                self._process_function(node)
            elif isinstance(node, ast.Call):
                self._process_call(node)
    
    def _process_import(self, node: ast.Import) -> None:
        """
        处理import语句
        
        Args:
            node: Import节点
        """
        for alias in node.names:
            self.imports.append({
                'file': self.current_file,
                'type': 'import',
                'module': alias.name,
                'alias': alias.asname
            })
    
    def _process_import_from(self, node: ast.ImportFrom) -> None:
        """
        处理from import语句
        
        Args:
            node: ImportFrom节点
        """
        module = node.module or ''
        for alias in node.names:
            self.imports.append({
                'file': self.current_file,
                'type': 'from_import',
                'module': module,
                'name': alias.name,
                'alias': alias.asname
            })
    
    def _process_class(self, node: ast.ClassDef) -> None:
        """
        处理类定义
        
        Args:
            node: ClassDef节点
        """
        class_name = node.name
        base_classes = [self._get_name(base) for base in node.bases]
        
        self.classes[class_name] = {
            'name': class_name,
            'file': self.current_file,
            'bases': base_classes,
            'methods': [],
            'line': node.lineno
        }
        
        self._class_stack.append(class_name)
        
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.classes[class_name]['methods'].append(item.name)
        
        self._class_stack.pop()
    
    def _process_function(self, node: ast.FunctionDef) -> None:
        """
        处理函数定义
        
        Args:
            node: FunctionDef节点
        """
        func_name = node.name
        args = [arg.arg for arg in node.args.args]
        
        self.functions[func_name] = {
            'name': func_name,
            'file': self.current_file,
            'args': args,
            'is_method': len(self._class_stack) > 0,
            'class': self._class_stack[-1] if self._class_stack else None,
            'line': node.lineno
        }
    
    def _process_call(self, node: ast.Call) -> None:
        """
        处理函数调用
        
        Args:
            node: Call节点
        """
        caller = self._get_caller_context()
        callee = self._get_name(node.func)
        
        if callee:
            self.calls.append({
                'file': self.current_file,
                'caller': caller,
                'callee': callee,
                'line': node.lineno
            })
    
    def _get_caller_context(self) -> str:
        """
        获取当前调用上下文
        
        Returns:
            调用者上下文
        """
        if self._class_stack:
            return self._class_stack[-1]
        return ''
    
    def _get_name(self, node: ast.AST) -> str:
        """
        从AST节点获取名称
        
        Args:
            node: AST节点
            
        Returns:
            名称字符串
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self._get_name(node.attr)
        elif isinstance(node, ast.FunctionDef):
            return node.name
        elif isinstance(node, ast.AsyncFunctionDef):
            return node.name
        elif isinstance(node, ast.ClassDef):
            return node.name
        return ''
    
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


class PythonDependencyAnalyzer:
    """
    Python依赖分析器，负责分析模块间的依赖关系和耦合度
    """
    
    def __init__(self, static_result: Dict[str, Any]):
        """
        初始化依赖分析器
        
        Args:
            static_result: 静态分析结果
        """
        self.static_result = static_result
        self.module_deps: Dict[str, Set[str]] = defaultdict(set)
        self.class_deps: Dict[str, Set[str]] = defaultdict(set)
        self.coupling_metrics: Dict[str, float] = {}
    
    def analyze(self) -> Dict[str, Any]:
        """
        执行依赖分析
        
        Returns:
            依赖分析结果
        """
        self._analyze_module_deps()
        self._analyze_class_deps()
        self._calculate_coupling()
        
        return {
            'module_dependencies': dict(self.module_deps),
            'class_dependencies': dict(self.class_deps),
            'coupling_metrics': self.coupling_metrics
        }
    
    def _analyze_module_deps(self) -> None:
        """
        分析模块间依赖
        """
        for imp in self.static_result.get('imports', []):
            file = imp.get('file', '')
            module = imp.get('module', '') or imp.get('name', '')
            if file and module:
                self.module_deps[file].add(module)
    
    def _analyze_class_deps(self) -> None:
        """
        分析类间依赖
        """
        classes = self.static_result.get('classes', {})
        for class_name, class_info in classes.items():
            for base in class_info.get('bases', []):
                if base in classes:
                    self.class_deps[class_name].add(base)
        
        for call in self.static_result.get('calls', []):
            caller = call.get('caller', '')
            callee = call.get('callee', '')
            if caller and callee in classes:
                self.class_deps[caller].add(callee)
    
    def _calculate_coupling(self) -> None:
        """
        计算模块耦合度
        """
        all_modules = set(self.module_deps.keys())
        for module in all_modules:
            deps = self.module_deps[module]
            self.coupling_metrics[module] = len(deps) / max(1, len(all_modules))
