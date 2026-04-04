"""
内置规则库
包含安全、业务、性能、AI幻觉等各类规则
"""

from gatekeeper_agent.models.rule import (
    Rule, RuleSet, Severity, Category, Trigger, ContextType,
    CascadeCheck, ValidationRule, ViolationResponse, RuleMetadata, FailAction
)


def create_builtin_rule_set() -> RuleSet:
    """创建内置规则集"""
    
    rules = [
        # ========== 高危操作规则 ==========
        
        # 1. 无 WHERE 条件的 DELETE
        Rule(
            rule_id="security-sql-001",
            name="无 WHERE 条件的 DELETE 语句",
            severity=Severity.FATAL,
            category=Category.SECURITY,
            description="检测到没有 WHERE 条件的 DELETE 语句，可能导致全表数据被删除",
            triggers=[
                Trigger(
                    pattern=r"DELETE\s+FROM\s+\w+",
                    language=["sql"],
                    context=ContextType.CODE,
                    file_pattern=["*.sql"]
                )
            ],
            cascade_checks=[
                CascadeCheck(
                    name="WHERE 条件检查",
                    description="检查 DELETE 语句是否包含 WHERE 条件",
                    validation=ValidationRule(
                        must_contain=[r"WHERE\s+"]
                    ),
                    fail_action=FailAction.BLOCK
                )
            ],
            violation_response=ViolationResponse(
                block_commit=True,
                message="【高危】检测到无 WHERE 条件的 DELETE 语句 ({rule_id})\n"
                        "文件: {file_path}\n"
                        "这可能导致全表数据被意外删除！\n"
                        "请添加 WHERE 条件限制删除范围。",
                suggested_fix="DELETE FROM table_name WHERE condition;",
                require_approval="sre-team"
            ),
            metadata=RuleMetadata(
                version="1.0",
                author="security-team",
                tags=["sql", "delete", "data-loss"]
            )
        ),
        
        # 2. 无 WHERE 条件的 UPDATE
        Rule(
            rule_id="security-sql-002",
            name="无 WHERE 条件的 UPDATE 语句",
            severity=Severity.FATAL,
            category=Category.SECURITY,
            description="检测到没有 WHERE 条件的 UPDATE 语句，可能导致全表数据被更新",
            triggers=[
                Trigger(
                    pattern=r"UPDATE\s+\w+\s+SET",
                    language=["sql"],
                    context=ContextType.CODE,
                    file_pattern=["*.sql"]
                )
            ],
            cascade_checks=[
                CascadeCheck(
                    name="WHERE 条件检查",
                    description="检查 UPDATE 语句是否包含 WHERE 条件",
                    validation=ValidationRule(
                        must_contain=[r"WHERE\s+"]
                    ),
                    fail_action=FailAction.BLOCK
                )
            ],
            violation_response=ViolationResponse(
                block_commit=True,
                message="【高危】检测到无 WHERE 条件的 UPDATE 语句 ({rule_id})\n"
                        "文件: {file_path}\n"
                        "这可能导致全表数据被意外更新！",
                suggested_fix="UPDATE table_name SET column=value WHERE condition;",
                require_approval="sre-team"
            ),
            metadata=RuleMetadata(
                version="1.0",
                author="security-team",
                tags=["sql", "update", "data-loss"]
            )
        ),
        
        # 3. rm -rf 命令
        Rule(
            rule_id="security-shell-001",
            name="危险的 rm -rf 命令",
            severity=Severity.FATAL,
            category=Category.SECURITY,
            description="检测到 rm -rf 命令，可能导致重要文件被强制删除",
            triggers=[
                Trigger(
                    pattern=r"rm\s+-[a-zA-Z]*rf|rm\s+-rf",
                    language=["shell", "bash"],
                    context=ContextType.CODE,
                    file_pattern=["*.sh", "*.bash"]
                ),
                Trigger(
                    pattern=r"os\.system\s*\(\s*['\"]rm\s+-[a-zA-Z]*rf",
                    language=["python"],
                    context=ContextType.CODE,
                    file_pattern=["*.py"]
                )
            ],
            cascade_checks=[
                CascadeCheck(
                    name="路径限制检查",
                    description="检查是否限定操作目录",
                    validation=ValidationRule(
                        must_not_contain=[r"rm\s+-[a-zA-Z]*rf\s+/\s*;", r"rm\s+-[a-zA-Z]*rf\s+/\s*$"]
                    ),
                    fail_action=FailAction.BLOCK
                ),
                CascadeCheck(
                    name="确认步骤检查",
                    description="检查是否有执行确认步骤",
                    validation=ValidationRule(
                        must_contain=[r"(confirm|prompt|read\s+-p|input\s*\()"]
                    ),
                    fail_action=FailAction.WARN
                )
            ],
            violation_response=ViolationResponse(
                block_commit=True,
                message="【高危】检测到 rm -rf 命令 ({rule_id})\n"
                        "文件: {file_path}\n"
                        "匹配内容: {match_content}\n"
                        "rm -rf 会强制递归删除文件且无法恢复！",
                suggested_fix="# 添加确认步骤\nread -p '确认删除? (y/n): ' confirm\nif [[ $confirm == [yY] ]]; then\n    rm -rf /path/to/target\nfi",
                require_approval="sre-team"
            ),
            metadata=RuleMetadata(
                version="1.0",
                author="security-team",
                tags=["shell", "rm", "data-loss"]
            )
        ),
        
        # 4. chmod 777
        Rule(
            rule_id="security-permission-001",
            name="过度宽松的文件权限",
            severity=Severity.ERROR,
            category=Category.SECURITY,
            description="检测到 chmod 777 命令，赋予所有用户完全权限",
            triggers=[
                Trigger(
                    pattern=r"chmod\s+777",
                    language=["shell", "bash"],
                    context=ContextType.CODE,
                    file_pattern=["*.sh", "*.bash"]
                ),
                Trigger(
                    pattern=r"os\.chmod\s*\([^,]+,\s*0o777",
                    language=["python"],
                    context=ContextType.CODE,
                    file_pattern=["*.py"]
                )
            ],
            violation_response=ViolationResponse(
                block_commit=False,
                message="【安全警告】检测到 chmod 777 ({rule_id})\n"
                        "文件: {file_path}\n"
                        "777 权限会赋予所有用户读写执行权限，存在安全风险！",
                suggested_fix="chmod 755 file_name  # 仅所有者可写\nchmod 644 file_name  # 仅所有者可读写",
                require_approval="sre-team"
            ),
            metadata=RuleMetadata(
                version="1.0",
                author="security-team",
                tags=["permission", "chmod", "security"]
            )
        ),
        
        # ========== 安全规则 ==========
        
        # 5. 硬编码密钥/密码
        Rule(
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
        ),
        
        # 6. SQL 注入风险
        Rule(
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
        ),
        
        # ========== 业务规则 ==========
        
        # 7. 权限校验缺失
        Rule(
            rule_id="business-auth-001",
            name="接口权限校验缺失",
            severity=Severity.ERROR,
            category=Category.BUSINESS,
            description="检测到可能缺少权限校验的接口定义",
            triggers=[
                Trigger(
                    pattern=r"@(app\.)?route\s*\([^)]+\)\s*\n\s*def\s+\w+",
                    language=["python"],
                    context=ContextType.CODE,
                    file_pattern=["*.py"]
                ),
                Trigger(
                    pattern=r"(router\.|app\.)\.(get|post|put|delete)\s*\([^)]+\)",
                    language=["javascript"],
                    context=ContextType.CODE,
                    file_pattern=["*.js", "*.ts"]
                )
            ],
            cascade_checks=[
                CascadeCheck(
                    name="权限装饰器检查",
                    description="检查是否添加了权限校验装饰器",
                    validation=ValidationRule(
                        must_contain=[r"@(require_auth|login_required|authenticate|permission|authorize)"]
                    ),
                    fail_action=FailAction.WARN
                )
            ],
            violation_response=ViolationResponse(
                block_commit=False,
                message="【业务警告】接口可能缺少权限校验 ({rule_id})\n"
                        "文件: {file_path}\n"
                        "请确保敏感接口已添加权限校验！",
                suggested_fix="@require_auth\n@app.route('/api/protected')\ndef protected_route():\n    pass",
                require_approval="tech-lead"
            ),
            metadata=RuleMetadata(
                version="1.0",
                author="business-team",
                tags=["auth", "permission", "api"]
            )
        ),
        
        # ========== 性能规则 ==========
        
        # 8. 数据库 N+1 查询
        Rule(
            rule_id="performance-db-001",
            name="潜在的 N+1 查询问题",
            severity=Severity.WARNING,
            category=Category.PERFORMANCE,
            description="检测到循环中可能存在数据库查询，可能导致 N+1 查询问题",
            triggers=[
                Trigger(
                    pattern=r"for\s+\w+\s+in\s+\w+:\s*\n\s+.*\.(get|filter|query|select)",
                    language=["python"],
                    context=ContextType.CODE,
                    file_pattern=["*.py"]
                )
            ],
            violation_response=ViolationResponse(
                block_commit=False,
                message="【性能提示】检测到潜在的 N+1 查询问题 ({rule_id})\n"
                        "文件: {file_path}\n"
                        "考虑使用 select_related 或 prefetch_related 优化查询",
                suggested_fix="# 使用 prefetch_related 优化\nusers = User.objects.prefetch_related('orders').all()\nfor user in users:\n    for order in user.orders.all():  # 不会产生额外查询\n        pass",
                require_approval=None
            ),
            metadata=RuleMetadata(
                version="1.0",
                author="performance-team",
                tags=["performance", "database", "n+1"]
            )
        ),
        
        # ========== AI 幻觉规则 ==========
        
        # 9. 不存在的 API 调用
        Rule(
            rule_id="ai-hallucination-001",
            name="可能存在幻觉的 API 调用",
            severity=Severity.WARNING,
            category=Category.AI_HALLUCINATION,
            description="检测到可能不存在的 API 调用或方法",
            triggers=[
                Trigger(
                    pattern=r"(OpenAI|ChatGPT|GPT-4|Claude|Gemini)\s*\.\s*\w+",
                    language=["python", "javascript"],
                    context=ContextType.CODE,
                    file_pattern=["*.py", "*.js", "*.ts"]
                )
            ],
            violation_response=ViolationResponse(
                block_commit=False,
                message="【AI 幻觉检查】检测到可能的幻觉 API 调用 ({rule_id})\n"
                        "文件: {file_path}\n"
                        "匹配内容: {match_content}\n"
                        "请验证该 API 是否存在！",
                suggested_fix=None,
                require_approval=None
            ),
            metadata=RuleMetadata(
                version="1.0",
                author="ai-team",
                ai_code_only=True,
                tags=["ai", "hallucination", "api"]
            )
        ),
        
        # 10. 逻辑矛盾代码
        Rule(
            rule_id="ai-hallucination-002",
            name="逻辑矛盾的代码",
            severity=Severity.WARNING,
            category=Category.AI_HALLUCINATION,
            description="检测到可能存在逻辑矛盾的代码",
            triggers=[
                Trigger(
                    pattern=r"if\s+\w+\s*:\s*\n\s+.*\n\s+if\s+not\s+\w+\s*:",
                    language=["python"],
                    context=ContextType.CODE,
                    file_pattern=["*.py"]
                )
            ],
            violation_response=ViolationResponse(
                block_commit=False,
                message="【AI 幻觉检查】检测到可能的逻辑矛盾 ({rule_id})\n"
                        "文件: {file_path}\n"
                        "请检查代码逻辑是否正确！",
                suggested_fix=None,
                require_approval=None
            ),
            metadata=RuleMetadata(
                version="1.0",
                author="ai-team",
                ai_code_only=True,
                tags=["ai", "hallucination", "logic"]
            )
        ),
    ]
    
    return RuleSet(
        name="Gatekeeper 内置规则集",
        description="AI Guardian Core 内置的安全、业务、性能审核规则",
        version="1.0.0",
        rules=rules
    )
