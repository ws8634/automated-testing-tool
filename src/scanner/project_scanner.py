import os
import ast
import json

class ProjectScanner:
    """项目扫描器，负责扫描本地项目文件夹，识别文件类型并提取基本信息"""
    
    def __init__(self, project_path):
        """
        初始化项目扫描器
        
        Args:
            project_path: 项目根目录路径
        """
        self.project_path = project_path
        self.files = []
    
    def scan(self):
        """
        扫描项目文件
        
        Returns:
            list: 扫描到的文件列表，每个元素包含文件路径和类型
        """
        for root, dirs, files in os.walk(self.project_path):
            # 排除一些不需要扫描的目录
            dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', 'venv', '__pycache__']]
            
            for file in files:
                file_path = os.path.join(root, file)
                file_type = self._get_file_type(file)
                if file_type:
                    self.files.append({
                        'path': file_path,
                        'type': file_type
                    })
        return self.files
    
    def _get_file_type(self, filename):
        """
        根据文件名判断文件类型
        
        Args:
            filename: 文件名
            
        Returns:
            str: 文件类型，如 'python', 'javascript', 'typescript' 或 None
        """
        if filename.endswith('.py'):
            return 'python'
        elif filename.endswith('.js'):
            return 'javascript'
        elif filename.endswith('.ts') or filename.endswith('.tsx'):
            return 'typescript'
        return None

class PythonScanner(ProjectScanner):
    """Python项目扫描器，负责解析Python文件的AST"""
    
    def scan(self):
        """
        扫描Python项目并解析AST
        
        Returns:
            list: 扫描到的文件列表，包含AST信息
        """
        files = super().scan()
        for file_info in files:
            if file_info['type'] == 'python':
                file_info['ast'] = self._parse_python_file(file_info['path'])
        return files
    
    def _parse_python_file(self, file_path):
        """
        解析Python文件的AST
        
        Args:
            file_path: Python文件路径
            
        Returns:
            ast.AST: 解析后的AST对象
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return ast.parse(content, filename=file_path)
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None