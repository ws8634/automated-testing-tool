import ast
import networkx as nx

class StaticAnalyzer:
    """静态分析器，负责分析代码的静态结构和依赖关系"""
    
    def __init__(self):
        """初始化静态分析器"""
        self.graph = nx.DiGraph()
    
    def analyze(self, files):
        """
        分析文件的静态结构
        
        Args:
            files: 扫描到的文件列表
        """
        for file_info in files:
            if file_info['type'] == 'python' and file_info.get('ast'):
                self._analyze_python_file(file_info)
    
    def _analyze_python_file(self, file_info):
        """
        分析Python文件的静态结构
        
        Args:
            file_info: 文件信息，包含路径和AST
        """
        visitor = PythonASTVisitor(self.graph, file_info['path'])
        visitor.visit(file_info['ast'])
    
    def get_graph(self):
        """
        获取构建的依赖图
        
        Returns:
            networkx.DiGraph: 依赖关系图
        """
        return self.graph

class PythonASTVisitor(ast.NodeVisitor):
    """Python AST访问器，用于遍历AST并提取依赖关系"""
    
    def __init__(self, graph, file_path):
        """
        初始化AST访问器
        
        Args:
            graph: 依赖关系图
            file_path: 当前文件路径
        """
        self.graph = graph
        self.file_path = file_path
        self.current_class = None
    
    def visit_ClassDef(self, node):
        """访问类定义节点"""
        class_name = node.name
        self.current_class = class_name
        # 添加类节点
        self.graph.add_node(class_name, type='class', file=self.file_path)
        # 处理基类
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_class = base.id
                self.graph.add_edge(class_name, base_class, type='inherits')
        # 继续访问类的子节点
        self.generic_visit(node)
        self.current_class = None
    
    def visit_FunctionDef(self, node):
        """访问函数定义节点"""
        func_name = node.name
        if self.current_class:
            full_func_name = f"{self.current_class}.{func_name}"
        else:
            full_func_name = func_name
        # 添加函数节点
        self.graph.add_node(full_func_name, type='function', file=self.file_path)
        if self.current_class:
            self.graph.add_edge(self.current_class, full_func_name, type='contains')
        # 继续访问函数的子节点
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """访问函数调用节点"""
        if isinstance(node.func, ast.Attribute):
            # 方法调用，如 obj.method()
            if isinstance(node.func.value, ast.Name):
                obj_name = node.func.value.id
                method_name = node.func.attr
                caller = self.current_class if self.current_class else 'global'
                self.graph.add_edge(caller, f"{obj_name}.{method_name}", type='calls')
        elif isinstance(node.func, ast.Name):
            # 函数调用，如 func()
            func_name = node.func.id
            caller = self.current_class if self.current_class else 'global'
            self.graph.add_edge(caller, func_name, type='calls')
        # 继续访问调用的子节点
        self.generic_visit(node)