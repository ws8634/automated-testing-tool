"""
后端API应用，提供REST接口供前端调用
"""
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
from pathlib import Path

app = Flask(__name__, static_folder='frontend')
CORS(app)

analysis_cache = {}


@app.route('/')
def index():
    """
    返回前端主页
    """
    return send_from_directory('frontend', 'index.html')


@app.route('/api/scan', methods=['POST'])
def scan_project():
    """
    扫描项目
    """
    data = request.json
    project_path = data.get('project_path', '')
    
    if not project_path or not os.path.exists(project_path):
        return jsonify({'error': '项目路径不存在'}), 400
    
    try:
        from analyzer.scanner.scanner import ProjectScanner
        scanner = ProjectScanner(project_path)
        scan_result = scanner.scan()
        return jsonify(scan_result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze/static', methods=['POST'])
def static_analyze():
    """
    静态分析
    """
    data = request.json
    project_path = data.get('project_path', '')
    
    if not project_path or not os.path.exists(project_path):
        return jsonify({'error': '项目路径不存在'}), 400
    
    try:
        from analyzer.scanner.scanner import ProjectScanner
        from analyzer.static_analyzer.python_analyzer import PythonStaticAnalyzer, PythonDependencyAnalyzer
        from analyzer.static_analyzer.js_analyzer import JavaScriptStaticAnalyzer
        
        scanner = ProjectScanner(project_path)
        scan_result = scanner.scan()
        
        static_result = {}
        
        if scan_result.get('project_type') == 'python':
            python_files = scanner.get_python_files()
            analyzer = PythonStaticAnalyzer(project_path)
            static_result = analyzer.analyze(python_files)
            
            dep_analyzer = PythonDependencyAnalyzer(static_result)
            dep_result = dep_analyzer.analyze()
            static_result['dependencies'] = dep_result
        
        elif scan_result.get('project_type') in ['javascript', 'typescript']:
            js_files = scanner.get_js_files() + scanner.get_ts_files()
            analyzer = JavaScriptStaticAnalyzer(project_path)
            static_result = analyzer.analyze(js_files)
        
        analysis_cache['static'] = static_result
        return jsonify(static_result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze/dynamic', methods=['POST'])
def dynamic_analyze():
    """
    动态分析
    """
    data = request.json
    project_path = data.get('project_path', '')
    entry_point = data.get('entry_point', '')
    
    if not project_path or not os.path.exists(project_path):
        return jsonify({'error': '项目路径不存在'}), 400
    
    try:
        from analyzer.dynamic_analyzer.tracer import DynamicAnalyzer
        analyzer = DynamicAnalyzer(project_path)
        dynamic_result = analyzer.analyze(entry_point)
        analysis_cache['dynamic'] = dynamic_result
        return jsonify(dynamic_result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/report/json', methods=['GET'])
def report_json():
    """
    获取JSON格式报告
    """
    static_result = analysis_cache.get('static', {})
    dynamic_result = analysis_cache.get('dynamic', {})
    
    from analyzer.relation_reporter.reporter import RelationReporter
    reporter = RelationReporter(static_result, dynamic_result)
    return reporter.to_json(), 200, {'Content-Type': 'application/json'}


@app.route('/api/report/markdown', methods=['GET'])
def report_markdown():
    """
    获取Markdown格式报告
    """
    static_result = analysis_cache.get('static', {})
    dynamic_result = analysis_cache.get('dynamic', {})
    
    from analyzer.relation_reporter.reporter import RelationReporter
    reporter = RelationReporter(static_result, dynamic_result)
    return reporter.to_markdown(), 200, {'Content-Type': 'text/markdown'}


@app.route('/api/report/graph', methods=['GET'])
def report_graph():
    """
    获取图数据
    """
    static_result = analysis_cache.get('static', {})
    dynamic_result = analysis_cache.get('dynamic', {})
    
    from analyzer.relation_reporter.reporter import RelationReporter
    reporter = RelationReporter(static_result, dynamic_result)
    return jsonify(reporter.to_graph_data())


@app.route('/api/report/knowledge_graph', methods=['GET'])
def report_knowledge_graph():
    """
    获取知识图谱
    """
    static_result = analysis_cache.get('static', {})
    
    from analyzer.relation_reporter.reporter import KnowledgeGraphBuilder
    builder = KnowledgeGraphBuilder()
    kg_data = builder.build_from_static(static_result)
    return jsonify(kg_data)


@app.route('/api/test/generate', methods=['POST'])
def generate_tests():
    """
    生成测试用例
    """
    data = request.json
    test_type = data.get('type', 'pytest')
    
    static_result = analysis_cache.get('static', {})
    dynamic_result = analysis_cache.get('dynamic', {})
    
    from analyzer.test_generator.generator import TestCaseGenerator
    generator = TestCaseGenerator(static_result, dynamic_result)
    
    if test_type == 'pytest':
        test_code = generator.generate_pytest_tests()
    elif test_type == 'e2e':
        test_code = generator.generate_e2e_tests()
    elif test_type == 'api':
        test_code = generator.generate_api_tests()
    elif test_type == 'ui':
        test_code = generator.generate_ui_tests()
    else:
        return jsonify({'error': '不支持的测试类型'}), 400
    
    return jsonify({
        'test_type': test_type,
        'test_code': test_code
    })


@app.route('/api/test/report', methods=['GET'])
def test_report():
    """
    获取测试报告
    """
    static_result = analysis_cache.get('static', {})
    dynamic_result = analysis_cache.get('dynamic', {})
    
    from analyzer.test_generator.generator import TestCaseGenerator
    generator = TestCaseGenerator(static_result, dynamic_result)
    report = generator.generate_test_report()
    return jsonify(report)


@app.route('/api/info', methods=['GET'])
def api_info():
    """
    获取API信息
    """
    return jsonify({
        'name': '自动化测试分析器',
        'version': '1.0.0',
        'supported_languages': ['python', 'javascript', 'typescript'],
        'features': [
            '项目扫描',
            '静态分析（AST解析）',
            '动态分析（运行时追踪）',
            '知识图谱生成',
            '测试用例生成'
        ]
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
