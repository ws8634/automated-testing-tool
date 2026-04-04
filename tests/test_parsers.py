"""
解析器测试
"""

import pytest
import tempfile
import os
from pathlib import Path

from gatekeeper_agent.parsers.file_parser import FileParser
from gatekeeper_agent.models.scan import CodeSnippet, SourceType


class TestFileParser:
    """文件解析器测试类"""
    
    @pytest.fixture
    def parser(self):
        """创建解析器实例"""
        return FileParser()
    
    @pytest.fixture
    def temp_python_file(self):
        """创建临时 Python 文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
def hello():
    print("Hello, World!")
    return True

if __name__ == "__main__":
    hello()
""")
            temp_path = f.name
        yield temp_path
        os.unlink(temp_path)
    
    def test_parse_file(self, parser, temp_python_file):
        """测试解析单个文件"""
        snippet = parser.parse_file(temp_python_file)
        
        assert snippet is not None
        assert snippet.language == "python"
        assert snippet.file_path == temp_python_file
        assert snippet.source_type == SourceType.FILE
        assert "hello" in snippet.content
    
    def test_parse_nonexistent_file(self, parser):
        """测试解析不存在的文件"""
        snippet = parser.parse_file("/nonexistent/file.py")
        assert snippet is None
    
    def test_get_language(self, parser):
        """测试语言识别"""
        test_cases = [
            ("test.py", "python"),
            ("test.js", "javascript"),
            ("test.ts", "typescript"),
            ("test.go", "go"),
            ("test.java", "java"),
            ("Dockerfile", "dockerfile"),
            ("test.unknown", "unknown"),
        ]
        
        for file_path, expected_lang in test_cases:
            lang = parser._get_language(file_path)
            assert lang == expected_lang, f"Failed for {file_path}"
    
    def test_parse_directory(self, parser):
        """测试解析目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建测试文件
            (Path(temp_dir) / "file1.py").write_text("print(1)")
            (Path(temp_dir) / "file2.js").write_text("console.log(2)")
            (Path(temp_dir) / "subdir").mkdir()
            (Path(temp_dir) / "subdir" / "file3.py").write_text("print(3)")
            
            snippets = parser.parse_directory(temp_dir)
            
            assert len(snippets) == 3
            
            # 检查语言识别
            languages = [s.language for s in snippets]
            assert "python" in languages
            assert "javascript" in languages
    
    def test_should_exclude(self, parser):
        """测试排除逻辑"""
        patterns = ["__pycache__", "*.pyc", "node_modules"]
        
        # 应该排除的路径
        assert parser._should_exclude("path/__pycache__/file.py", patterns)
        assert parser._should_exclude("path/test.pyc", patterns)
        assert parser._should_exclude("node_modules/package/file.js", patterns)
        
        # 不应该排除的路径
        assert not parser._should_exclude("path/src/file.py", patterns)
        assert not parser._should_exclude("test.py", patterns)


class TestGitParser:
    """Git 解析器测试类"""
    
    @pytest.fixture
    def git_parser(self):
        """创建 Git 解析器实例"""
        from gatekeeper_agent.parsers.git_parser import GitParser
        return GitParser()
    
    def test_get_language(self, git_parser):
        """测试语言识别"""
        # Git 解析器和文件解析器使用相同的映射
        test_cases = [
            ("src/main.py", "python"),
            ("lib/utils.js", "javascript"),
            ("cmd/app.go", "go"),
        ]
        
        for file_path, expected_lang in test_cases:
            lang = git_parser._get_language(file_path)
            assert lang == expected_lang


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
