"""
规则加载器

作者: Claude 3.5 Sonnet (Anthropic)
版本: 0.1.0
创建时间: 2026-03-14

功能目标:
    - 支持从 YAML 文件加载规则
    - 管理内置规则和自定义规则
    - 提供规则集的合并和查询功能

对应需求:
    1. 规则管理 - 支持规则的新增/禁用/版本管理
    2. 自定义规则 - 支持业务团队添加专属规则
"""

import os
import yaml
from pathlib import Path
from typing import List, Optional, Dict, Any

from gatekeeper_agent.models.rule import Rule, RuleSet
from gatekeeper_agent.utils.logger import get_logger

logger = get_logger(__name__)


class RuleLoader:
    """规则加载器"""
    
    def __init__(self, rules_dir: Optional[str] = None):
        self.rules_dir = rules_dir or self._get_default_rules_dir()
    
    def _get_default_rules_dir(self) -> str:
        """获取默认规则目录"""
        # 首先检查环境变量
        env_dir = os.environ.get('GATEKEEPER_RULES_DIR')
        if env_dir:
            return env_dir
        
        # 然后检查项目目录
        package_dir = Path(__file__).parent.parent
        rules_dir = package_dir / 'config' / 'rules'
        
        if rules_dir.exists():
            return str(rules_dir)
        
        # 最后检查当前目录
        return str(Path.cwd() / '.gatekeeper' / 'rules')
    
    def load_from_yaml(self, file_path: str) -> Optional[RuleSet]:
        """
        从 YAML 文件加载规则集
        
        Args:
            file_path: YAML 文件路径
            
        Returns:
            Optional[RuleSet]: 规则集，加载失败返回 None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            
            if not data:
                logger.warning(f"YAML 文件为空: {file_path}")
                return None
            
            # 如果是单个规则，包装成规则集
            if 'rules' not in data and 'rule_id' in data:
                data = {
                    'name': 'Single Rule',
                    'description': '单个规则',
                    'version': '1.0.0',
                    'rules': [data]
                }
            
            rule_set = RuleSet.model_validate(data)
            logger.info(f"从 {file_path} 加载了 {len(rule_set.rules)} 条规则")
            return rule_set
            
        except Exception as e:
            logger.error(f"加载 YAML 文件失败 {file_path}: {e}")
            return None
    
    def load_from_directory(self, dir_path: Optional[str] = None) -> RuleSet:
        """
        从目录加载所有规则文件
        
        Args:
            dir_path: 规则目录路径，默认使用初始化时设置的目录
            
        Returns:
            RuleSet: 合并后的规则集
        """
        dir_path = dir_path or self.rules_dir
        path = Path(dir_path)
        
        if not path.exists():
            logger.warning(f"规则目录不存在: {dir_path}")
            return RuleSet(
                name="Empty",
                description="空规则集",
                version="1.0.0",
                rules=[]
            )
        
        all_rules = []
        
        # 遍历目录中的所有 YAML 文件
        for yaml_file in path.rglob('*.yaml'):
            if yaml_file.name.endswith('.yaml') or yaml_file.name.endswith('.yml'):
                rule_set = self.load_from_yaml(str(yaml_file))
                if rule_set:
                    all_rules.extend(rule_set.rules)
        
        for yml_file in path.rglob('*.yml'):
            rule_set = self.load_from_yaml(str(yml_file))
            if rule_set:
                all_rules.extend(rule_set.rules)
        
        merged_rule_set = RuleSet(
            name="Loaded Rules",
            description=f"从 {dir_path} 加载的规则",
            version="1.0.0",
            rules=all_rules
        )
        
        logger.info(f"从目录 {dir_path} 加载了共 {len(all_rules)} 条规则")
        return merged_rule_set
    
    def save_to_yaml(self, rule_set: RuleSet, file_path: str) -> bool:
        """
        保存规则集到 YAML 文件
        
        Args:
            rule_set: 规则集
            file_path: 输出文件路径
            
        Returns:
            bool: 是否保存成功
        """
        try:
            # 转换为字典
            data = rule_set.model_dump()
            
            # 确保目录存在
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 写入 YAML
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, sort_keys=False)
            
            logger.info(f"规则集已保存到: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"保存规则集失败: {e}")
            return False


def load_builtin_rules() -> RuleSet:
    """
    加载内置规则
    
    从分类模块加载所有规则:
        - high_risk: 高危操作规则
        - security: 安全规则
        - business: 业务规则
        - performance: 性能规则
        - ai_hallucination: AI幻觉规则
        - supply_chain: 供应链安全规则
    
    Returns:
        RuleSet: 合并后的内置规则集
    """
    from gatekeeper_agent.rules.builtin import (
        get_high_risk_rules,
        get_security_rules,
        get_business_rules,
        get_performance_rules,
        get_ai_hallucination_rules,
        get_supply_chain_rules,
    )
    
    all_rules = []
    
    # 加载各类规则
    all_rules.extend(get_high_risk_rules())
    all_rules.extend(get_security_rules())
    all_rules.extend(get_business_rules())
    all_rules.extend(get_performance_rules())
    all_rules.extend(get_ai_hallucination_rules())
    all_rules.extend(get_supply_chain_rules())
    
    return RuleSet(
        name="Gatekeeper 内置规则集",
        description="AI Guardian Core 内置的安全、业务、性能审核规则",
        version="1.0.0",
        rules=all_rules
    )


def load_rules(
    builtin: bool = True,
    custom_dir: Optional[str] = None
) -> RuleSet:
    """
    加载规则
    
    Args:
        builtin: 是否加载内置规则
        custom_dir: 自定义规则目录
        
    Returns:
        RuleSet: 合并后的规则集
    """
    all_rules = []
    
    # 加载内置规则
    if builtin:
        builtin_rules = load_builtin_rules()
        all_rules.extend(builtin_rules.rules)
    
    # 加载自定义规则
    if custom_dir:
        loader = RuleLoader(custom_dir)
        custom_rules = loader.load_from_directory()
        all_rules.extend(custom_rules.rules)
    else:
        # 尝试加载默认目录的规则
        loader = RuleLoader()
        default_rules = loader.load_from_directory()
        all_rules.extend(default_rules.rules)
    
    return RuleSet(
        name="Merged Rules",
        description="合并的规则集",
        version="1.0.0",
        rules=all_rules
    )
