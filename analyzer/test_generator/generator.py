"""
测试用例生成器，基于调用关系自动生成端到端测试用例
"""
from typing import Dict, Any, List
from collections import defaultdict


class TestCaseGenerator:
    """
    测试用例生成器，负责基于代码分析结果生成测试用例
    """
    
    def __init__(self, static_result: Dict[str, Any] = None, dynamic_result: Dict[str, Any] = None):
        """
        初始化测试用例生成器
        
        Args:
            static_result: 静态分析结果
            dynamic_result: 动态分析结果
        """
        self.static_result = static_result or {}
        self.dynamic_result = dynamic_result or {}
    
    def set_results(self, static_result: Dict[str, Any], dynamic_result: Dict[str, Any]) -> None:
        """
        设置分析结果
        
        Args:
            static_result: 静态分析结果
            dynamic_result: 动态分析结果
        """
        self.static_result = static_result
        self.dynamic_result = dynamic_result
    
    def generate_pytest_tests(self) -> str:
        """
        生成pytest格式的测试用例
        
        Returns:
            测试用例代码字符串
        """
        lines = []
        lines.append('"""')
        lines.append('自动生成的测试用例')
        lines.append('"""')
        lines.append('import pytest')
        lines.append('')
        
        classes = self.static_result.get('classes', {})
        for class_name, class_info in classes.items():
            lines.append(f'')
            lines.append(f'class Test{class_name}:')
            lines.append(f'    """测试{class_name}类"""')
            lines.append(f'')
            
            for method in class_info.get('methods', []):
                lines.append(f'    def test_{method}(self):')
                lines.append(f'        """测试{method}方法"""')
                lines.append(f'        # TODO: 实现测试逻辑')
                lines.append(f'        pass')
                lines.append(f'')
        
        functions = self.static_result.get('functions', {})
        for func_name, func_info in functions.items():
            if not func_info.get('is_method'):
                lines.append(f'')
                lines.append(f'def test_{func_name}():')
                lines.append(f'    """测试{func_name}函数"""')
                lines.append(f'    # TODO: 实现测试逻辑')
                lines.append(f'    pass')
                lines.append(f'')
        
        return '\n'.join(lines)
    
    def generate_e2e_tests(self) -> str:
        """
        生成端到端测试用例
        
        Returns:
            测试用例代码字符串
        """
        lines = []
        lines.append('"""')
        lines.append('端到端测试用例')
        lines.append('"""')
        lines.append('import pytest')
        lines.append('')
        
        call_chains = self._extract_call_chains()
        
        for i, chain in enumerate(call_chains):
            if len(chain) >= 2:
                test_name = f'test_e2e_chain_{i}'
                lines.append(f'')
                lines.append(f'def {test_name}():')
                lines.append(f'    """测试调用链: {" -> ".join(chain)}"""')
                lines.append(f'    # TODO: 实现端到端测试逻辑')
                lines.append(f'    # 执行完整的调用链并验证结果')
                lines.append(f'    pass')
                lines.append(f'')
        
        return '\n'.join(lines)
    
    def generate_api_tests(self) -> str:
        """
        生成API测试用例
        
        Returns:
            测试用例代码字符串
        """
        lines = []
        lines.append('"""')
        lines.append('API测试用例')
        lines.append('"""')
        lines.append('import pytest')
        lines.append('import requests')
        lines.append('')
        
        api_calls = self.dynamic_result.get('api_calls', [])
        
        for i, api_call in enumerate(api_calls):
            test_name = f'test_api_{i}'
            lines.append(f'')
            lines.append(f'def {test_name}():')
            lines.append(f'    """测试API: {api_call.get("url", "")}"""')
            lines.append(f'    # TODO: 实现API测试逻辑')
            lines.append(f'    # response = requests.get("{api_call.get("url", "")}")')
            lines.append(f'    # assert response.status_code == 200')
            lines.append(f'    pass')
            lines.append(f'')
        
        return '\n'.join(lines)
    
    def generate_ui_tests(self) -> str:
        """
        生成UI测试用例
        
        Returns:
            测试用例代码字符串
        """
        lines = []
        lines.append('"""')
        lines.append('UI测试用例')
        lines.append('"""')
        lines.append('import pytest')
        lines.append('from selenium import webdriver')
        lines.append('')
        
        lines.append(f'')
        lines.append(f'class TestUI:')
        lines.append(f'    """UI测试类"""')
        lines.append(f'')
        lines.append(f'    @pytest.fixture')
        lines.append(f'    def driver(self):')
        lines.append(f'        driver = webdriver.Chrome()')
        lines.append(f'        yield driver')
        lines.append(f'        driver.quit()')
        lines.append(f'')
        lines.append(f'    def test_page_navigation(self, driver):')
        lines.append(f'        """测试页面导航"""')
        lines.append(f'        # TODO: 实现UI测试逻辑')
        lines.append(f'        # driver.get("http://localhost:8000")')
        lines.append(f'        pass')
        lines.append(f'')
        
        return '\n'.join(lines)
    
    def _extract_call_chains(self) -> List[List[str]]:
        """
        提取调用链
        
        Returns:
            调用链列表
        """
        call_graph = self.dynamic_result.get('call_graph', {})
        edges = call_graph.get('edges', {})
        
        chains = []
        visited = set()
        
        def dfs(node, path):
            if node in visited:
                return
            visited.add(node)
            path.append(node)
            
            if node in edges:
                for callee in edges[node]:
                    dfs(callee.get('to', ''), path.copy())
            else:
                chains.append(path.copy())
        
        for node in edges:
            if node not in visited:
                dfs(node, [])
        
        return chains
    
    def generate_test_report(self) -> Dict[str, Any]:
        """
        生成测试报告
        
        Returns:
            测试报告字典
        """
        call_chains = self._extract_call_chains()
        
        return {
            'summary': {
                'total_classes': self.static_result.get('class_count', 0),
                'total_functions': self.static_result.get('function_count', 0),
                'total_calls': self.static_result.get('call_count', 0),
                'call_chains_count': len(call_chains)
            },
            'test_cases': {
                'unit_tests': self.static_result.get('class_count', 0) + self.static_result.get('function_count', 0),
                'e2e_tests': len(call_chains),
                'api_tests': len(self.dynamic_result.get('api_calls', [])),
                'ui_tests': 1
            },
            'call_chains': call_chains
        }


class TestCoverageAnalyzer:
    """
    测试覆盖率分析器，负责分析测试覆盖情况
    """
    
    def __init__(self, static_result: Dict[str, Any]):
        """
        初始化测试覆盖率分析器
        
        Args:
            static_result: 静态分析结果
        """
        self.static_result = static_result
    
    def analyze(self, test_files: List[str]) -> Dict[str, Any]:
        """
        分析测试覆盖率
        
        Args:
            test_files: 测试文件列表
            
        Returns:
            覆盖率分析结果
        """
        classes = self.static_result.get('classes', {})
        functions = self.static_result.get('functions', {})
        
        covered_classes = set()
        covered_functions = set()
        
        for test_file in test_files:
            try:
                with open(test_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for class_name in classes:
                    if f'Test{class_name}' in content or f'test_{class_name}' in content:
                        covered_classes.add(class_name)
                
                for func_name in functions:
                    if f'test_{func_name}' in content:
                        covered_functions.add(func_name)
            
            except Exception as e:
                print(f"分析测试文件 {test_file} 时出错: {e}")
        
        total_classes = len(classes)
        total_functions = len(functions)
        
        return {
            'classes': {
                'total': total_classes,
                'covered': len(covered_classes),
                'coverage': len(covered_classes) / total_classes if total_classes > 0 else 0.0,
                'covered_list': list(covered_classes),
                'uncovered_list': [c for c in classes if c not in covered_classes]
            },
            'functions': {
                'total': total_functions,
                'covered': len(covered_functions),
                'coverage': len(covered_functions) / total_functions if total_functions > 0 else 0.0,
                'covered_list': list(covered_functions),
                'uncovered_list': [f for f in functions if f not in covered_functions]
            }
        }
