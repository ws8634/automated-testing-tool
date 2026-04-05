from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.scanner.project_scanner import ProjectScanner, PythonScanner
from src.analyzer.static_analyzer import StaticAnalyzer
from src.analyzer.dynamic_analyzer import DynamicAnalyzer
from src.generator.test_generator import TestGenerator, DocumentationGenerator
import os
import json

app = Flask(__name__)
CORS(app)

@app.route('/api/scan', methods=['POST'])
def scan_project():
    """
    扫描项目
    """
    data = request.json
    project_path = data.get('project_path')
    
    if not project_path or not os.path.exists(project_path):
        return jsonify({'error': 'Invalid project path'}), 400
    
    scanner = PythonScanner(project_path)
    files = scanner.scan()
    
    # 构建文件树结构
    file_tree = build_file_tree(files, project_path)
    
    return jsonify({
        'files': files,
        'file_tree': file_tree
    })

@app.route('/api/analyze', methods=['POST'])
def analyze_project():
    """
    分析项目
    """
    data = request.json
    project_path = data.get('project_path')
    
    if not project_path or not os.path.exists(project_path):
        return jsonify({'error': 'Invalid project path'}), 400
    
    # 静态分析
    scanner = PythonScanner(project_path)
    files = scanner.scan()
    
    static_analyzer = StaticAnalyzer()
    static_analyzer.analyze(files)
    static_graph = static_analyzer.get_graph()
    
    # 动态分析（这里只是示例，实际需要运行代码）
    dynamic_analyzer = DynamicAnalyzer()
    # 这里应该运行项目代码以收集动态调用关系
    # dynamic_analyzer.start_tracing()
    # run_project_code()
    # dynamic_analyzer.stop_tracing()
    # dynamic_graph = dynamic_analyzer.get_graph()
    dynamic_graph = None
    
    # 生成文档
    doc_generator = DocumentationGenerator(static_graph, dynamic_graph)
    output_dir = os.path.join(os.getcwd(), 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    json_output = os.path.join(output_dir, 'relations.json')
    markdown_output = os.path.join(output_dir, 'relations.md')
    
    doc_generator.generate_json(json_output)
    doc_generator.generate_markdown(markdown_output)
    
    # 生成测试用例
    test_generator = TestGenerator(static_graph, dynamic_graph)
    tests = test_generator.generate_tests()
    
    # 构建图数据
    graph_data = {
        'nodes': [],
        'edges': []
    }
    
    for node, data in static_graph.nodes(data=True):
        graph_data['nodes'].append({
            'id': node,
            'label': node,
            'type': data.get('type', 'unknown')
        })
    
    for u, v, data in static_graph.edges(data=True):
        graph_data['edges'].append({
            'source': u,
            'target': v,
            'label': data.get('type', 'unknown')
        })
    
    return jsonify({
        'graph': graph_data,
        'tests': tests,
        'documentation': {
            'json': json_output,
            'markdown': markdown_output
        }
    })

def build_file_tree(files, project_path):
    """
    构建文件树结构
    
    Args:
        files: 扫描到的文件列表
        project_path: 项目根目录路径
        
    Returns:
        dict: 文件树结构
    """
    tree = {}
    
    for file_info in files:
        relative_path = os.path.relpath(file_info['path'], project_path)
        parts = relative_path.split(os.sep)
        
        current = tree
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        current[parts[-1]] = file_info['type']
    
    return tree

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)