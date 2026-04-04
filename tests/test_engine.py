"""
规则引擎测试
"""

import pytest
from gatekeeper_agent.models.rule import RuleSet, Severity, Category
from gatekeeper_agent.models.scan import CodeSnippet, SourceType
from gatekeeper_agent.core.engine import RuleEngine


class TestRuleEngine:
    """规则引擎测试类"""
    
    @pytest.fixture
    def sample_rule_set(self):
        """创建示例规则集"""
        from gatekeeper_agent.rules.builtin_rules import create_builtin_rule_set
        return create_builtin_rule_set()
    
    @pytest.fixture
    def engine(self, sample_rule_set):
        """创建规则引擎实例"""
        return RuleEngine(sample_rule_set)
    
    def test_engine_initialization(self, sample_rule_set):
        """测试引擎初始化"""
        engine = RuleEngine(sample_rule_set)
        assert engine.rule_set == sample_rule_set
        assert len(engine._compiled_patterns) > 0
    
    def test_scan_safe_code(self, engine):
        """测试扫描安全代码"""
        code = """
def hello_world():
    print("Hello, World!")
    return True
"""
        snippet = CodeSnippet(
            content=code,
            language="python",
            file_path="test.py",
            line_start=1,
            line_end=4,
            source_type=SourceType.FILE
        )
        
        result = engine.scan(snippet)
        
        assert result.scan_id is not None
        assert result.source_type == SourceType.FILE
        assert result.summary.total_violations == 0
    
    def test_scan_dangerous_delete(self, engine):
        """测试扫描危险的 DELETE 语句"""
        code = """
-- 危险的删除操作
DELETE FROM users;
"""
        snippet = CodeSnippet(
            content=code,
            language="sql",
            file_path="test.sql",
            line_start=1,
            line_end=3,
            source_type=SourceType.FILE
        )
        
        result = engine.scan(snippet)
        
        # 应该检测到违规
        violations = result.get_violations_by_severity("fatal")
        assert len(violations) > 0
        
        # 检查是否是 DELETE 规则
        delete_violations = [v for v in violations if "DELETE" in v.rule_name]
        assert len(delete_violations) > 0
    
    def test_scan_hardcoded_secret(self, engine):
        """测试扫描硬编码密钥"""
        code = """
# 硬编码密码（危险）
password = "my_secret_password_123"
api_key = "sk-1234567890abcdef"
"""
        snippet = CodeSnippet(
            content=code,
            language="python",
            file_path="config.py",
            line_start=1,
            line_end=4,
            source_type=SourceType.FILE
        )
        
        result = engine.scan(snippet)
        
        # 应该检测到违规
        violations = result.violations
        secret_violations = [v for v in violations if "密钥" in v.rule_name or "secret" in v.rule_name.lower()]
        assert len(secret_violations) > 0
    
    def test_scan_rm_rf(self, engine):
        """测试扫描 rm -rf 命令"""
        code = """
#!/bin/bash
# 危险的操作
rm -rf /important/data
"""
        snippet = CodeSnippet(
            content=code,
            language="shell",
            file_path="cleanup.sh",
            line_start=1,
            line_end=4,
            source_type=SourceType.FILE
        )
        
        result = engine.scan(snippet)
        
        # 应该检测到违规
        violations = result.get_violations_by_severity("fatal")
        rm_violations = [v for v in violations if "rm" in v.rule_name.lower()]
        assert len(rm_violations) > 0
    
    def test_batch_scan(self, engine):
        """测试批量扫描"""
        snippets = [
            CodeSnippet(
                content="print('hello')",
                language="python",
                file_path="file1.py",
                line_start=1,
                line_end=1,
                source_type=SourceType.FILE
            ),
            CodeSnippet(
                content="password = 'secret'",
                language="python",
                file_path="file2.py",
                line_start=1,
                line_end=1,
                source_type=SourceType.FILE
            )
        ]
        
        result = engine.scan_batch(snippets)
        
        assert result.summary.total_files == 2
        assert result.summary.total_violations >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
