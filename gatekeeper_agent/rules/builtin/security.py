"""
安全规则

作者: Claude 3.5 Sonnet (Anthropic)
版本: 0.1.0
创建时间: 2026-03-14

包含规则:
    【FATAL级别 - 阻断提交】
    1. security-secret-001: 硬编码密钥或密码 (生产环境密钥)
    2. security-injection-001: SQL 注入风险
    3. security-secret-004: 私钥文件内容检测

    【ERROR级别 - 需审批】
    4. security-secret-002: 测试环境密钥硬编码
    5. security-permission-001: 过度宽松的文件权限 (chmod 777)
    6. security-permission-002: 敏感文件权限暴露
    7. security-cors-001: 过于宽松的 CORS 配置

    【WARNING级别 - 仅提示】
    8. security-secret-003: 配置文件中的敏感字段
    9. security-log-001: 敏感信息日志打印

    【INFO级别 - 仅记录】
    10. security-config-001: 调试模式启用
"""

from typing import List
from gatekeeper_agent.models.rule import (
    Rule, Severity, Category, Trigger, ContextType,
    CascadeCheck, ValidationRule, ViolationResponse, RuleMetadata, FailAction
)


def get_security_rules() -> List[Rule]:
    """获取安全规则列表"""
    return [
        # FATAL级别
        _get_hardcoded_secret_rule(),
        _get_sql_injection_rule(),
        _get_private_key_rule(),
        # ERROR级别
        _get_test_secret_rule(),
        _get_chmod_777_rule(),
        _get_sensitive_file_permission_rule(),
        _get_cors_misconfig_rule(),
        # WARNING级别
        _get_config_secret_rule(),
        _get_sensitive_log_rule(),
        # INFO级别
        _get_debug_mode_rule(),
    ]


def _get_hardcoded_secret_rule() -> Rule:
    """硬编码密钥或密码"""
    return Rule(
        rule_id="security-secret-001",
        name="硬编码密钥或密码",
        severity=Severity.ERROR,
        category=Category.SECURITY,
        description="检测到可能的硬编码密钥、密码或敏感信息",
        triggers=[
            Trigger(
                pattern=r"(password|passwd|pwd|secret|key|token|api_key)\s*=\s*['\"][^'\"]{4,}['\"]",
                language=["python", "javascript", "go", "java"],
                context=ContextType.CODE,
                file_pattern=["*.py", "*.js", "*.ts", "*.go", "*.java"]
            ),
            Trigger(
                pattern=r"(AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY|PRIVATE_KEY|SECRET_KEY)\s*=\s*['\"][^'\"]+['\"]",
                language=["python", "javascript", "go", "shell"],
                context=ContextType.CODE,
                file_pattern=["*.py", "*.js", "*.ts", "*.go", "*.sh"]
            )
        ],
        cascade_checks=[
            CascadeCheck(
                name="环境变量检查",
                description="检查是否使用环境变量",
                validation=ValidationRule(
                    must_contain=[r"os\.environ|process\.env|os\.Getenv|System\.getenv"]
                ),
                fail_action=FailAction.UPGRADE_SEVERITY
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【安全警告】检测到可能的硬编码敏感信息 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "匹配内容: {match_content}\n"
                    "请勿在代码中硬编码密钥、密码等敏感信息！",
            suggested_fix="# 使用环境变量\nimport os\npassword = os.environ.get('DB_PASSWORD')",
            require_approval="security-team"
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["secret", "password", "security", "hardcoded"]
        )
    )


def _get_sql_injection_rule() -> Rule:
    """SQL 注入风险"""
    return Rule(
        rule_id="security-injection-001",
        name="SQL 注入风险",
        severity=Severity.ERROR,
        category=Category.SECURITY,
        description="检测到可能的 SQL 注入漏洞，使用字符串拼接构建 SQL 查询",
        triggers=[
            Trigger(
                pattern=r"(execute|query|raw)\s*\(\s*['\"].*%s.*['\"]\s*%",
                language=["python"],
                context=ContextType.CODE,
                file_pattern=["*.py"]
            ),
            Trigger(
                pattern=r"(execute|query)\s*\(\s*['\"].*\+.*\+.*['\"]",
                language=["python", "javascript"],
                context=ContextType.CODE,
                file_pattern=["*.py", "*.js", "*.ts"]
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【安全警告】检测到 SQL 注入风险 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "请勿使用字符串拼接构建 SQL 查询！",
            suggested_fix="# 使用参数化查询\ncursor.execute('SELECT * FROM users WHERE id = %s', (user_id,))",
            require_approval="security-team"
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["sql-injection", "security"]
        )
    )


def _get_private_key_rule() -> Rule:
    """私钥文件内容检测 - FATAL级别"""
    return Rule(
        rule_id="security-secret-004",
        name="私钥文件内容检测",
        severity=Severity.FATAL,
        category=Category.SECURITY,
        description="检测到私钥文件内容（RSA/SSH/SSL私钥），必须立即移除",
        triggers=[
            Trigger(
                pattern=r"-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
                language=["*"],
                context=ContextType.CODE,
                file_pattern=["*"]
            ),
            Trigger(
                pattern=r"-----BEGIN CERTIFICATE-----",
                language=["*"],
                context=ContextType.CODE,
                file_pattern=["*"]
            )
        ],
        violation_response=ViolationResponse(
            block_commit=True,
            message="【严重安全漏洞】检测到私钥文件内容 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "私钥绝对不允许提交到代码仓库！",
            suggested_fix="# 将私钥添加到 .gitignore\n# 使用环境变量或密钥管理服务",
            require_approval=None
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["private-key", "certificate", "fatal", "security"]
        )
    )


def _get_test_secret_rule() -> Rule:
    """测试环境密钥硬编码 - ERROR级别"""
    return Rule(
        rule_id="security-secret-002",
        name="测试环境密钥硬编码",
        severity=Severity.ERROR,
        category=Category.SECURITY,
        description="检测到测试环境配置硬编码，建议统一配置管理",
        triggers=[
            Trigger(
                pattern=r"(test_|dev_|staging_)(password|secret|key|token)\s*=\s*['\"][^'\"]+['\"]",
                language=["python", "javascript", "go", "java"],
                context=ContextType.CODE,
                file_pattern=["*.py", "*.js", "*.ts", "*.go", "*.java"]
            ),
            Trigger(
                pattern=r"TEST_(PASSWORD|SECRET|KEY|TOKEN)\s*=\s*['\"][^'\"]+['\"]",
                language=["python", "javascript", "go", "shell"],
                context=ContextType.CODE,
                file_pattern=["*.py", "*.js", "*.ts", "*.go", "*.sh"]
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【安全建议】检测到测试环境密钥硬编码 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "即使是测试环境，也建议使用统一配置管理",
            suggested_fix="# 使用环境变量\nimport os\ntest_password = os.environ.get('TEST_DB_PASSWORD', 'default_test_pass')",
            require_approval="security-team"
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["test-secret", "configuration", "security"]
        )
    )


def _get_chmod_777_rule() -> Rule:
    """过度宽松的文件权限 - ERROR级别"""
    return Rule(
        rule_id="security-permission-001",
        name="过度宽松的文件权限",
        severity=Severity.ERROR,
        category=Category.SECURITY,
        description="检测到 chmod 777 或等效的全开放权限设置",
        triggers=[
            Trigger(
                pattern=r"chmod\s+(-R\s+)?777",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"os\.chmod\s*\([^)]*,\s*0o777\s*\)",
                language=["python"],
                context=ContextType.CODE,
                file_pattern=["*.py"]
            ),
            Trigger(
                pattern=r"fs\.chmod\s*\([^)]*,\s*0o777\s*\)",
                language=["javascript"],
                context=ContextType.CODE,
                file_pattern=["*.js", "*.ts"]
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【权限风险】检测到过度宽松的文件权限设置 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "777权限允许任何用户读写执行，存在严重安全隐患",
            suggested_fix="# 使用最小权限原则\nos.chmod('/path/to/file', 0o644)  # 仅所有者可写\n# 或\nos.chmod('/path/to/file', 0o755)  # 可执行但仅所有者可写",
            require_approval="security-team"
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["permission", "chmod", "security"]
        )
    )


def _get_sensitive_file_permission_rule() -> Rule:
    """敏感文件权限暴露 - ERROR级别"""
    return Rule(
        rule_id="security-permission-002",
        name="敏感文件权限暴露",
        severity=Severity.ERROR,
        category=Category.SECURITY,
        description="敏感配置文件（.env, config等）权限设置不当",
        triggers=[
            Trigger(
                pattern=r"(\.env|config\.json|secrets\.yaml|credentials)\s+\d{3}",
                language=["shell"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"(\.env|config\.json|secrets)\b.*?(chmod|permission)",
                language=["python", "javascript"],
                context=ContextType.CODE,
                file_pattern=["*.py", "*.js", "*.ts"]
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【权限风险】敏感文件权限配置需审查 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "敏感配置文件应限制为仅所有者可读写",
            suggested_fix="# 敏感文件应设置为600权限\nos.chmod('.env', 0o600)",
            require_approval="security-team"
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["permission", "sensitive-file", "security"]
        )
    )


def _get_cors_misconfig_rule() -> Rule:
    """过于宽松的 CORS 配置 - ERROR级别"""
    return Rule(
        rule_id="security-cors-001",
        name="过于宽松的 CORS 配置",
        severity=Severity.ERROR,
        category=Category.SECURITY,
        description="检测到允许任意来源的 CORS 配置",
        triggers=[
            Trigger(
                pattern=r"(Access-Control-Allow-Origin|CORS_ORIGIN)\s*[=:]\s*['\"]\*['\"]",
                language=["python", "javascript", "go", "java"],
                context=ContextType.CODE,
                file_pattern=["*.py", "*.js", "*.ts", "*.go", "*.java"]
            ),
            Trigger(
                pattern=r"cors\s*\(\s*.*?origin\s*[=:]\s*['\"]\*['\"]",
                language=["python", "javascript"],
                context=ContextType.CODE,
                file_pattern=["*.py", "*.js", "*.ts"]
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【CORS风险】检测到过于宽松的跨域配置 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "允许任意来源(*)可能导致CSRF攻击",
            suggested_fix="# 限制允许的域名\nCORS_ORIGIN = ['https://app.example.com', 'https://admin.example.com']",
            require_approval="security-team"
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["cors", "csrf", "security"]
        )
    )


def _get_config_secret_rule() -> Rule:
    """配置文件中的敏感字段 - WARNING级别"""
    return Rule(
        rule_id="security-secret-003",
        name="配置文件中的敏感字段",
        severity=Severity.WARNING,
        category=Category.SECURITY,
        description="配置文件(.yaml/.json/.ini)中包含可能的敏感字段",
        triggers=[
            Trigger(
                pattern=r"^(password|secret|key|token):\s*[^${}]+",
                language=["yaml"],
                context=ContextType.CODE,
                file_pattern=["*.yaml", "*.yml"]
            ),
            Trigger(
                pattern=r'"(password|secret|key|token)":\s*"[^${}"]+"',
                language=["json"],
                context=ContextType.CODE,
                file_pattern=["*.json"]
            ),
            Trigger(
                pattern=r"^(password|secret|key|token)\s*=\s*[^${}]+",
                language=["ini"],
                context=ContextType.CODE,
                file_pattern=["*.ini", "*.conf"]
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【配置警告】配置文件中包含敏感字段 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "建议使用占位符或环境变量引用",
            suggested_fix="# 使用环境变量占位符\npassword: ${DB_PASSWORD}\n# 或\nsecret: ${{ secrets.API_KEY }}",
            require_approval=None
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["config", "secret", "warning"]
        )
    )


def _get_sensitive_log_rule() -> Rule:
    """敏感信息日志打印 - WARNING级别"""
    return Rule(
        rule_id="security-log-001",
        name="敏感信息日志打印",
        severity=Severity.WARNING,
        category=Category.SECURITY,
        description="日志输出中包含可能的敏感信息",
        triggers=[
            Trigger(
                pattern=r"(log|logger|print|console)\.[a-z]+\s*\([^)]*(password|secret|token|key|credential)",
                language=["python", "javascript", "go", "java"],
                context=ContextType.CODE,
                file_pattern=["*.py", "*.js", "*.ts", "*.go", "*.java"]
            ),
            Trigger(
                pattern=r"(LOG|LOGGER)\.\w+\s*\([^)]*(PASSWORD|SECRET|TOKEN|KEY)",
                language=["go", "java"],
                context=ContextType.CODE,
                file_pattern=["*.go", "*.java"]
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【日志风险】检测到敏感信息可能输出到日志 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "避免在日志中打印密码、密钥等敏感信息",
            suggested_fix="# 脱敏处理\nlogger.info(f\"User login: {username}, password: ****\")\n# 或只记录非敏感字段\nlogger.info(f\"User login attempt: {username}\")",
            require_approval=None
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["logging", "sensitive-data", "warning"]
        )
    )


def _get_debug_mode_rule() -> Rule:
    """调试模式启用 - INFO级别"""
    return Rule(
        rule_id="security-config-001",
        name="调试模式启用",
        severity=Severity.INFO,
        category=Category.SECURITY,
        description="检测到调试模式或详细错误输出配置",
        triggers=[
            Trigger(
                pattern=r"(DEBUG|debug)\s*[=:]\s*(True|true|1)",
                language=["python", "javascript", "go", "yaml"],
                context=ContextType.CODE,
                file_pattern=["*.py", "*.js", "*.ts", "*.go", "*.yaml", "*.yml"]
            ),
            Trigger(
                pattern=r"(app\.run\s*\(.*debug\s*=\s*True)",
                language=["python"],
                context=ContextType.CODE,
                file_pattern=["*.py"]
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【配置提示】检测到调试模式启用 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "确保生产环境已关闭调试模式",
            suggested_fix="# 生产环境配置\nDEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'",
            require_approval=None
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["debug", "configuration", "info"]
        )
    )
