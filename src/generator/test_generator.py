import networkx as nx
import json
import os

class TestGenerator:
    """测试用例生成器，基于调用关系生成端到端测试用例"""
    
    def __init__(self, static_graph, dynamic_graph=None):
        """
        初始化测试生成器
        
        Args:
            static_graph: 静态分析生成的依赖图
            dynamic_graph: 动态分析生成的调用图
        """
        self.static_graph = static_graph
        self.dynamic_graph = dynamic_graph
    
    def generate_tests(self):
        """
        生成测试用例
        
        Returns:
            list: 生成的测试用例列表
        """
        tests = []
        # 基于静态分析生成测试用例
        tests.extend(self._generate_static_tests())
        # 基于动态分析生成测试用例
        if self.dynamic_graph:
            tests.extend(self._generate_dynamic_tests())
        return tests
    
    def _generate_static_tests(self):
        """
        基于静态分析生成测试用例
        
        Returns:
            list: 生成的测试用例列表
        """
        tests = []
        # 遍历所有函数节点
        for node, data in self.static_graph.nodes(data=True):
            if data.get('type') == 'function':
                test = {
                    'name': f"test_{node}",
                    'target': node,
                    'description': f"Test {node}",
                    'steps': [f"Call {node}"]
                }
                tests.append(test)
        return tests
    
    def _generate_dynamic_tests(self):
        """
        基于动态分析生成测试用例
        
        Returns:
            list: 生成的测试用例列表
        """
        tests = []
        # 遍历所有函数节点
        for node, data in self.dynamic_graph.nodes(data=True):
            if data.get('type') == 'function':
                # 找到调用该函数的所有节点
                predecessors = list(self.dynamic_graph.predecessors(node))
                if predecessors:
                    test = {
                        'name': f"test_dynamic_{node}",
                        'target': node,
                        'description': f"Dynamic test for {node}",
                        'steps': [f"Call {pred} which calls {node}" for pred in predecessors[:2]]
                    }
                    tests.append(test)
        return tests

class DocumentationGenerator:
    """文档生成器，生成调用关系文档"""
    
    def __init__(self, static_graph, dynamic_graph=None):
        """
        初始化文档生成器
        
        Args:
            static_graph: 静态分析生成的依赖图
            dynamic_graph: 动态分析生成的调用图
        """
        self.static_graph = static_graph
        self.dynamic_graph = dynamic_graph
    
    def generate_json(self, output_path):
        """
        生成JSON格式的调用关系文档
        
        Args:
            output_path: 输出文件路径
        """
        data = {
            'static_relations': self._graph_to_json(self.static_graph),
            'dynamic_relations': self._graph_to_json(self.dynamic_graph) if self.dynamic_graph else {}
        }
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    
    def generate_markdown(self, output_path):
        """
        生成Markdown格式的调用关系文档
        
        Args:
            output_path: 输出文件路径
        """
        markdown = "# 调用关系文档\n\n"
        
        # 静态关系
        markdown += "## 静态关系\n\n"
        markdown += self._graph_to_markdown(self.static_graph)
        
        # 动态关系
        if self.dynamic_graph:
            markdown += "\n## 动态关系\n\n"
            markdown += self._graph_to_markdown(self.dynamic_graph)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)
    
    def _graph_to_json(self, graph):
        """
        将图转换为JSON格式
        
        Args:
            graph: 关系图
            
        Returns:
            dict: JSON格式的关系数据
        """
        nodes = []
        edges = []
        
        for node, data in graph.nodes(data=True):
            nodes.append({
                'id': node,
                'data': data
            })
        
        for u, v, data in graph.edges(data=True):
            edges.append({
                'source': u,
                'target': v,
                'data': data
            })
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    def _graph_to_markdown(self, graph):
        """
        将图转换为Markdown格式
        
        Args:
            graph: 关系图
            
        Returns:
            str: Markdown格式的关系数据
        """
        markdown = "### 节点\n\n"
        
        for node, data in graph.nodes(data=True):
            markdown += f"- **{node}** ({data.get('type', 'unknown')})"
            if 'file' in data:
                markdown += f" - {data['file']}"
            markdown += "\n"
        
        markdown += "\n### 边\n\n"
        
        for u, v, data in graph.edges(data=True):
            markdown += f"- **{u}** -> **{v}** ({data.get('type', 'unknown')})\n"
        
        return markdown