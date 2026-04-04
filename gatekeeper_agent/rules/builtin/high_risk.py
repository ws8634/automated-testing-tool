"""
高危操作规则

作者: Claude 3.5 Sonnet (Anthropic)
版本: 0.1.0
创建时间: 2026-03-14

包含规则:
    【FATAL级别 - 阻断提交】
    1. security-sql-001: 无 WHERE 条件的 DELETE 语句
    2. security-sql-002: 无 WHERE 条件的 UPDATE 语句
    3. security-shell-001: 危险的 rm -rf 命令
    4. security-shell-003: 危险的 dd 磁盘操作命令
    5. security-shell-004: 危险的 mkfs 格式化命令

    【ERROR级别 - 需审批】
    6. security-shell-002: 无限制的 sudo 命令
    7. security-k8s-001: 危险的 Kubernetes 删除命令
    8. security-docker-001: 危险的 Docker 强制操作
"""


from typing import List
from gatekeeper_agent.models.rule import (
    Rule, Severity, Category, Trigger, ContextType,
    CascadeCheck, ValidationRule, ViolationResponse, RuleMetadata, FailAction
)


def get_high_risk_rules() -> List[Rule]:
    """获取高危操作规则列表"""
    return [
        # FATAL级别
        _get_delete_without_where_rule(),
        _get_update_without_where_rule(),
        _get_rm_rule(),
        _get_dd_rule(),
        _get_mkfs_rule(),
        # ERROR级别
        _get_sudo_rule(),
        _get_kubectl_delete_rule(),
        _get_docker_force_rule(),
    ]


def _get_delete_without_where_rule() -> Rule:
    """无 WHERE 条件的 DELETE 语句"""
    return Rule(
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
            tags=["sql", "delete", "data-loss", "high-risk"]
        )
    )


def _get_update_without_where_rule() -> Rule:
    """无 WHERE 条件的 UPDATE 语句"""
    return Rule(
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
            tags=["sql", "update", "data-loss", "high-risk"]
        )
    )


def _get_rm_rule() -> Rule:
    """危险的 rm 命令"""
    return Rule(
        rule_id="security-shell-001",
        name="危险的文件删除命令",
        severity=Severity.FATAL,
        category=Category.SECURITY,
        description="检测到 rm 删除命令，强制删除(-f)或递归删除(-r/-rf)可能导致重要文件丢失",
        triggers=[
            Trigger(
                pattern=r"^\s*rm\s+(-[a-zA-Z]*[rf]|--force|--recursive)",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash", "*.zsh"]
            ),
            Trigger(
                pattern=r"['\"]?rm\s+-[a-zA-Z]*[rf]",
                language=["python"],
                context=ContextType.CODE,
                file_pattern=["*.py"]
            )
        ],
        cascade_checks=[
            CascadeCheck(
                name="根目录保护检查",
                description="检查是否尝试删除根目录或系统关键目录",
                validation=ValidationRule(
                    must_not_contain=[
                        r"rm\s+-[a-zA-Z]*[rf]\s+/\s*;?\s*$",
                        r"rm\s+-[a-zA-Z]*[rf]\s+/\s*;",
                        r"rm\s+-[a-zA-Z]*[rf]\s+/bin",
                        r"rm\s+-[a-zA-Z]*[rf]\s+/etc",
                        r"rm\s+-[a-zA-Z]*[rf]\s+/usr",
                        r"rm\s+-[a-zA-Z]*[rf]\s+/var",
                        r"rm\s+-[a-zA-Z]*[rf]\s+/home\s*$"
                    ]
                ),
                fail_action=FailAction.BLOCK
            ),
            CascadeCheck(
                name="通配符检查",
                description="检查是否使用危险的通配符",
                validation=ValidationRule(
                    must_not_contain=[r"rm\s+-[a-zA-Z]*[rf].*\*.*", r"rm\s+-[a-zA-Z]*[rf].*\?.*"]
                ),
                fail_action=FailAction.UPGRADE_SEVERITY
            ),
            CascadeCheck(
                name="确认步骤检查",
                description="检查是否有执行确认步骤",
                validation=ValidationRule(
                    must_contain=[r"(confirm|prompt|read\s+-p|input\s*\(|--interactive)"]
                ),
                fail_action=FailAction.WARN
            )
        ],
        violation_response=ViolationResponse(
            block_commit=True,
            message="【高危】检测到危险的文件删除命令 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "匹配内容: {match_content}\n"
                    "rm -f/-r/-rf 会强制删除文件且无法恢复，请谨慎使用！",
            suggested_fix="# 添加确认步骤\nread -p '确认删除? (y/n): ' confirm\nif [[ $confirm == [yY] ]]; then\n    rm -f /path/to/target\nfi",
            require_approval="sre-team"
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["shell", "rm", "delete", "data-loss", "high-risk"]
        )
    )


def _get_sudo_rule() -> Rule:
    """危险的 sudo 命令"""
    return Rule(
        rule_id="security-shell-002",
        name="无限制的 sudo 命令",
        severity=Severity.ERROR,
        category=Category.SECURITY,
        description="检测到 sudo 命令，可能以 root 权限执行危险操作",
        triggers=[
            Trigger(
                pattern=r"\bsudo\s+(rm|dd|mkfs|fdisk|parted|reboot|shutdown|init\s+0|poweroff)",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"os\.system\s*\(\s*['\"]sudo\s+(rm|dd|mkfs|fdisk|parted)",
                language=["python"],
                context=ContextType.CODE,
                file_pattern=["*.py"]
            )
        ],
        cascade_checks=[
            CascadeCheck(
                name="用户确认检查",
                description="检查是否有用户确认步骤",
                validation=ValidationRule(
                    must_contain=[r"(confirm|prompt|read\s+-p|input\s*\()"]
                ),
                fail_action=FailAction.WARN
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【安全警告】检测到 sudo 执行高危命令 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "匹配内容: {match_content}\n"
                    "sudo 以 root 权限执行，请确保操作安全！",
            suggested_fix="# 添加确认步骤\nread -p '确认执行sudo操作? (y/n): ' confirm\nif [[ $confirm == [yY] ]]; then\n    sudo rm -f /path/to/file\nfi",
            require_approval="sre-team"
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["shell", "sudo", "root", "security", "high-risk"]
        )
    )


def _get_dd_rule() -> Rule:
    """危险的 dd 命令"""
    return Rule(
        rule_id="security-shell-003",
        name="危险的磁盘操作命令",
        severity=Severity.FATAL,
        category=Category.SECURITY,
        description="检测到 dd 命令，可能直接操作磁盘设备导致数据丢失",
        triggers=[
            Trigger(
                pattern=r"\bdd\s+if\s*=\s*\S+\s+of\s*=\s*(/dev/[sh]d[a-z]|/dev/nvme|/dev/mmcblk|/dev/disk)",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"\bdd\s+.*of\s*=\s*/dev/[sh]d[a-z]",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            )
        ],
        cascade_checks=[
            CascadeCheck(
                name="系统盘保护检查",
                description="检查是否操作系统盘",
                validation=ValidationRule(
                    must_not_contain=[r"of\s*=\s*/dev/[sh]da\b", r"of\s*=\s*/dev/nvme0n1\b"]
                ),
                fail_action=FailAction.BLOCK
            ),
            CascadeCheck(
                name="确认步骤检查",
                description="检查是否有用户确认",
                validation=ValidationRule(
                    must_contain=[r"(confirm|prompt|read\s+-p|input\s*\()"]
                ),
                fail_action=FailAction.WARN
            )
        ],
        violation_response=ViolationResponse(
            block_commit=True,
            message="【高危】检测到 dd 磁盘操作命令 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "匹配内容: {match_content}\n"
                    "dd 直接操作磁盘，可能导致数据永久丢失！",
            suggested_fix="# 添加确认步骤\necho '警告: 这将操作磁盘设备!'\nread -p '确认继续? (yes/no): ' confirm\nif [[ $confirm == 'yes' ]]; then\n    dd if=/path/to/source of=/path/to/target bs=4M\nfi",
            require_approval="sre-team"
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["shell", "dd", "disk", "data-loss", "high-risk"]
        )
    )


def _get_mkfs_rule() -> Rule:
    """危险的文件系统格式化命令"""
    return Rule(
        rule_id="security-shell-004",
        name="危险的文件系统格式化命令",
        severity=Severity.FATAL,
        category=Category.SECURITY,
        description="检测到 mkfs 命令，可能格式化磁盘分区导致数据丢失",
        triggers=[
            Trigger(
                pattern=r"\bmkfs\.[a-z]+\s+/dev/[sh]d[a-z]\d*",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"\bmkfs\s+-t\s+\w+\s+/dev/[sh]d[a-z]\d*",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            )
        ],
        cascade_checks=[
            CascadeCheck(
                name="系统盘保护检查",
                description="检查是否格式化系统盘",
                validation=ValidationRule(
                    must_not_contain=[r"/dev/[sh]da\d*\b", r"/dev/nvme0n1\b"]
                ),
                fail_action=FailAction.BLOCK
            )
        ],
        violation_response=ViolationResponse(
            block_commit=True,
            message="【高危】检测到文件系统格式化命令 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "匹配内容: {match_content}\n"
                    "mkfs 会格式化磁盘，导致数据永久丢失！",
            suggested_fix="# 添加确认步骤\necho '警告: 这将格式化磁盘分区!'\nread -p '确认继续? (yes/no): ' confirm\nif [[ $confirm == 'yes' ]]; then\n    mkfs.ext4 /dev/sdb1\nfi",
            require_approval="sre-team"
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="security-team",
            tags=["shell", "mkfs", "format", "disk", "data-loss", "high-risk"]
        )
    )


def _get_kubectl_delete_rule() -> Rule:
    """危险的 kubectl delete 命令"""
    return Rule(
        rule_id="security-k8s-001",
        name="危险的 Kubernetes 删除命令",
        severity=Severity.ERROR,
        category=Category.SECURITY,
        description="检测到 kubectl delete 命令，可能删除生产环境资源",
        triggers=[
            Trigger(
                pattern=r"kubectl\s+delete\s+(pod|deployment|service|namespace|pvc|pv|secret|configmap)",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash", "*.yaml", "*.yml"]
            ),
            Trigger(
                pattern=r"kubectl\s+delete\s+-f\s+\S+",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"kubectl\s+delete\s+--all",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            )
        ],
        cascade_checks=[
            CascadeCheck(
                name="命名空间检查",
                description="检查是否在 production 命名空间操作",
                validation=ValidationRule(
                    must_not_contain=[r"-n\s+production", r"--namespace\s+production", r"-n\s+prod", r"--namespace\s+prod"]
                ),
                fail_action=FailAction.UPGRADE_SEVERITY
            ),
            CascadeCheck(
                name="强制删除检查",
                description="检查是否使用 --force --grace-period=0 强制删除",
                validation=ValidationRule(
                    must_not_contain=[r"--force.*--grace-period.*0", r"--grace-period.*0.*--force"]
                ),
                fail_action=FailAction.BLOCK
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【安全警告】检测到 kubectl delete 命令 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "匹配内容: {match_content}\n"
                    "删除 Kubernetes 资源可能影响服务运行！",
            suggested_fix="# 先确认资源\nkubectl get pods -n namespace\n# 再删除\nkubectl delete pod pod-name -n namespace",
            require_approval="k8s-admin"
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="k8s-team",
            tags=["kubernetes", "kubectl", "delete", "k8s", "high-risk"]
        )
    )


def _get_docker_force_rule() -> Rule:
    """危险的 Docker 强制操作"""
    return Rule(
        rule_id="security-docker-001",
        name="危险的 Docker 强制操作",
        severity=Severity.ERROR,
        category=Category.SECURITY,
        description="检测到 Docker 强制删除或清理命令，可能删除正在运行的容器",
        triggers=[
            Trigger(
                pattern=r"docker\s+rm\s+-f",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"docker\s+rmi\s+-f",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"docker\s+system\s+prune\s+-f",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            ),
            Trigger(
                pattern=r"docker\s+container\s+prune\s+-f",
                language=["shell", "bash"],
                context=ContextType.CODE,
                file_pattern=["*.sh", "*.bash"]
            )
        ],
        cascade_checks=[
            CascadeCheck(
                name="生产环境检查",
                description="检查是否在生产环境使用",
                validation=ValidationRule(
                    must_not_contain=[r"#.*prod", r"#.*production", r"ENV.*production"]
                ),
                fail_action=FailAction.WARN
            )
        ],
        violation_response=ViolationResponse(
            block_commit=False,
            message="【安全警告】检测到 Docker 强制操作 ({rule_id})\n"
                    "文件: {file_path}\n"
                    "匹配内容: {match_content}\n"
                    "强制删除可能导致正在运行的服务中断！",
            suggested_fix="# 先停止容器\ndocker stop container-name\n# 再删除\ndocker rm container-name",
            require_approval="devops-team"
        ),
        metadata=RuleMetadata(
            version="1.0",
            author="devops-team",
            tags=["docker", "container", "force", "high-risk"]
        )
    )
