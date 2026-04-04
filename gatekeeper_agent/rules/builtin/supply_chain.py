"""
供应链安全规则

作者: Claude 3.5 Sonnet (Anthropic)
版本: 0.1.0
创建时间: 2026-03-14

参考: OpenClaw 安全建议 - 供应链攻击防范

包含规则:
    1. supply-chain-001: 远程脚本下载执行
    2. supply-chain-002: 动态代码执行
    3. supply-chain-003: Base64 解码执行
    4. supply-chain-004: 管道符危险组合
"""

from typing import List
from gatekeeper_agent.models.rule import (
    Rule, Severity, Category, Trigger, ContextType,
    CascadeCheck, ValidationRule, ViolationResponse, RuleMetadata, FailAction
)


def get_supply_chain_rules() -> List[Rule]:
    """获取供应链安全规则列表"""
    return [
        _get_remote_script_rule(),
        _get_dynamic_exec_rule(),
        _get_base64_exec_rule(),
        _get_dangerous_pipe_rule(),
    ]


def _get_remote_script_rule() -> Rule:
    """远程脚本下载执行"""
    return Rule(
        rule_id="supply-chain-001",
        name="远程脚本下载执行风险",
        severity=Severity.FATAL,
        category=Category.SECURITY,
        description="检测到从远程下载脚本并直接执行，存在供应链攻击风险",
        triggers=[
            Trigger(
                pattern=r"(curl|wget)\s+.*\|\s*(bash|sh|python|python3)",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"(curl|wget)\s+.*\s+-O\s*-\s*\|\s*(bash|sh)",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"(curl|wget)\s+.*\s*&&\s*(bash|sh|python)",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"os\.system\s*\(\s*['\"](curl|wget)",
                language=["python"],
                context=ContextType.CODE,
                file_pattern=["*.py"]
            ),
            Trigger(
                pattern=r"subprocess\.\w+\s*\(\s*['\"](curl|wget)",
                language=["python"],
                context=ContextType.CODE,
                file_pattern=["*.py"]
            )
        ],
        cascade_checks=[
            CascadeCheck(
                name="HTTPS 检查",
                description="检查是否使用 HTTPS 下载",
                validation=ValidationRule(
                    must_contain=[r"https://"]
                ),
                fail_action=FailAction.UPGRADE_SEVERITY
            ),
            CascadeCheck(
                name="签名验证检查",
                description="检查是否有签名验证",
                validation=ValidationRule(
                    must_contain=[r"(checksum|sha256|md5|gpg|verify)"]
                ),
                fail_action=FailAction.WARN
            )
        ],
        violation_response=ViolationResponse(
            block_commit=True,
            message="【高危】检测到远程脚本下载执行 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "匹配内容: {match_content}\n"
                    "从远程下载并执行脚本存在供应链攻击风险！\n"
                    "建议: 1. 使用 HTTPS 下载\n"
                    "      2. 验证脚本签名或校验和\n"
                    "      3. 在沙箱环境中执行",
            suggested_fix="# 安全下载示例\nurl=\"https://example.com/script.sh\"\ncurl -fsSL \"$url\" -o script.sh\n# 验证校验和\nsha256sum -c script.sh.sha256\n# 审查后再执行\nbash script.sh",
            require_approval="security-team"
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["supply-chain", "remote-script", "curl", "wget", "high-risk"]
        )
    )


def _get_dynamic_exec_rule() -> Rule:
    """动态代码执行"""
    return Rule(
        rule_id="supply-chain-002",
        name="动态代码执行风险",
        severity=Severity.ERROR,
        category=Category.SECURITY,
        description="检测到 eval/exec 等动态代码执行，可能被恶意利用",
        triggers=[
            Trigger(
                pattern=r"\beval\s*\(",
                language=["python", "javascript", "shell"],
                context=ContextType.CODE,
                file_pattern=["*.py", "*.js", "*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"\bexec\s*\(",
                language=["python", "javascript"],
                context=ContextType.CODE,
                file_pattern=["*.py", "*.js"]
            ),
            Trigger(
                pattern=r"\bexec\s+\$",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"new\s+Function\s*\(",
                language=["javascript"],
                context=ContextType.CODE,
                file_pattern=["*.js"]
            )
        ],
        cascade_checks=[
            CascadeCheck(
                name="用户输入检查",
                description="检查是否执行用户输入",
                validation=ValidationRule(
                    must_not_contain=[r"(input|request|params|args|argv)"]
                ),
                fail_action=FailAction.BLOCK
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【安全警告】检测到动态代码执行 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "匹配内容: {match_content}\n"
                    "eval/exec 可能执行恶意代码，存在代码注入风险！",
            suggested_fix="# 使用更安全的替代方案\n# 而不是: eval(user_input)\n# 使用: json.loads(user_input) 或 ast.literal_eval(user_input)",
            require_approval="security-team"
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["supply-chain", "eval", "exec", "code-injection", "high-risk"]
        )
    )


def _get_base64_exec_rule() -> Rule:
    """Base64 解码执行"""
    return Rule(
        rule_id="supply-chain-003",
        name="Base64 解码执行风险",
        severity=Severity.ERROR,
        category=Category.SECURITY,
        description="检测到 Base64 解码后执行，可能隐藏恶意代码",
        triggers=[
            Trigger(
                pattern=r"base64\s+.*\|\s*(bash|sh|python)",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"echo\s+.*\|\s*base64\s+-d\s*\|\s*(bash|sh)",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"base64\.b64decode\s*\(.*\).*exec",
                language=["python"],
                context=ContextType.CODE,
                file_pattern=["*.py"]
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【安全警告】检测到 Base64 解码执行 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "匹配内容: {match_content}\n"
                    "Base64 编码可能用于隐藏恶意代码！",
            suggested_fix="# 解码后先审查内容\necho \"base64encoded\" | base64 -d > decoded.sh\n# 审查内容\ncat decoded.sh\n# 确认安全后再执行\nbash decoded.sh",
            require_approval="security-team"
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["supply-chain", "base64", "obfuscation", "high-risk"]
        )
    )


def _get_dangerous_pipe_rule() -> Rule:
    """管道符危险组合"""
    return Rule(
        rule_id="supply-chain-004",
        name="危险的管道命令组合",
        severity=Severity.ERROR,
        category=Category.SECURITY,
        description="检测到危险的管道命令组合，可能绕过安全检查",
        triggers=[
            Trigger(
                pattern=r"(curl|wget).*\|.*sudo",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"(curl|wget).*\|.*sh\s+-c",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"wget\s+-q\s+-O-\s+.*\|",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【安全警告】检测到危险的管道命令组合 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "匹配内容: {match_content}\n"
                    "管道组合可能绕过安全检查，直接执行远程代码！",
            suggested_fix="# 先下载再审查\ncurl -fsSL https://example.com/script.sh -o script.sh\ncat script.sh  # 审查内容\nbash script.sh",
            require_approval="security-team"
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["supply-chain", "pipe", "curl", "sudo", "high-risk"]
        )
    )
