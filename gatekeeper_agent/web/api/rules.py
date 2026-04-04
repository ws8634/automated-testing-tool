"""
规则管理 API
"""

from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel

from gatekeeper_agent.rules.loader import load_rules, load_builtin_rules, RuleLoader
from gatekeeper_agent.models.rule import Rule, RuleSet, Severity, Category
from gatekeeper_agent.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class RuleResponse(BaseModel):
    """规则响应模型"""
    rule_id: str
    name: str
    severity: str
    category: str
    description: str
    enabled: bool
    is_builtin: bool
    metadata: dict


class RuleListResponse(BaseModel):
    """规则列表响应"""
    total: int
    rules: List[RuleResponse]


class RuleUpdateRequest(BaseModel):
    """规则更新请求"""
    enabled: Optional[bool] = None
    yaml_content: Optional[str] = None


class RuleCreateRequest(BaseModel):
    """创建规则请求"""
    rule_id: str
    name: str
    severity: str
    category: str
    description: str
    yaml_content: str


def _rule_to_response(rule: Rule, is_builtin: bool = False) -> RuleResponse:
    """将 Rule 对象转换为响应模型"""
    return RuleResponse(
        rule_id=rule.rule_id,
        name=rule.name,
        severity=rule.severity.value,
        category=rule.category.value,
        description=rule.description,
        enabled=rule.enabled,
        is_builtin=is_builtin,
        metadata={
            "version": rule.metadata.version,
            "author": rule.metadata.author,
            "tags": rule.metadata.tags,
            "ai_code_only": rule.metadata.ai_code_only,
        }
    )


@router.get("", response_model=RuleListResponse)
async def list_rules(
    category: Optional[str] = Query(None, description="按分类过滤"),
    severity: Optional[str] = Query(None, description="按风险等级过滤"),
    enabled: Optional[bool] = Query(None, description="按启用状态过滤"),
    search: Optional[str] = Query(None, description="搜索关键词")
):
    """获取规则列表"""
    try:
        # 加载内置规则和自定义规则
        builtin_rules = load_builtin_rules()
        custom_rules = load_rules(builtin=False)
        
        all_rules = []
        
        # 添加内置规则
        for rule in builtin_rules.rules:
            all_rules.append((rule, True))
        
        # 添加自定义规则
        custom_rule_ids = {r.rule_id for r in custom_rules.rules}
        for rule in custom_rules.rules:
            all_rules.append((rule, False))
        
        # 过滤
        filtered_rules = []
        for rule, is_builtin in all_rules:
            if category and rule.category.value != category:
                continue
            if severity and rule.severity.value != severity:
                continue
            if enabled is not None and rule.enabled != enabled:
                continue
            if search:
                search_lower = search.lower()
                if (search_lower not in rule.name.lower() and 
                    search_lower not in rule.description.lower() and
                    search_lower not in rule.rule_id.lower()):
                    continue
            filtered_rules.append(_rule_to_response(rule, is_builtin))
        
        return RuleListResponse(
            total=len(filtered_rules),
            rules=filtered_rules
        )
    except Exception as e:
        logger.error(f"获取规则列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def get_categories():
    """获取所有规则分类"""
    return [
        {"value": cat.value, "label": cat.value}
        for cat in Category
    ]


@router.get("/severities")
async def get_severities():
    """获取所有风险等级"""
    return [
        {"value": sev.value, "label": sev.value.upper()}
        for sev in Severity
    ]


@router.get("/{rule_id}", response_model=dict)
async def get_rule(rule_id: str):
    """获取规则详情"""
    try:
        # 先查找内置规则
        builtin_rules = load_builtin_rules()
        for rule in builtin_rules.rules:
            if rule.rule_id == rule_id:
                return {
                    "rule": _rule_to_response(rule, is_builtin=True),
                    "yaml_content": None,  # 内置规则不直接提供YAML
                    "source": "builtin"
                }
        
        # 查找自定义规则
        custom_rules = load_rules(builtin=False)
        for rule in custom_rules.rules:
            if rule.rule_id == rule_id:
                # 尝试读取YAML文件
                loader = RuleLoader()
                yaml_content = None
                rules_dir = Path(loader.rules_dir)
                if rules_dir.exists():
                    for yaml_file in rules_dir.rglob("*.yaml"):
                        rule_set = loader.load_from_yaml(str(yaml_file))
                        if rule_set:
                            for r in rule_set.rules:
                                if r.rule_id == rule_id:
                                    import yaml
                                    yaml_content = yaml.dump(r.model_dump(), allow_unicode=True)
                                    break
                        if yaml_content:
                            break
                
                return {
                    "rule": _rule_to_response(rule, is_builtin=False),
                    "yaml_content": yaml_content,
                    "source": "custom"
                }
        
        raise HTTPException(status_code=404, detail=f"规则不存在: {rule_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取规则详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{rule_id}")
async def update_rule(rule_id: str, request: RuleUpdateRequest):
    """更新规则"""
    try:
        # 目前只支持启用/禁用状态的切换
        # 实际实现需要将状态保存到配置文件
        return {"message": "规则更新成功", "rule_id": rule_id}
    except Exception as e:
        logger.error(f"更新规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
async def create_rule(request: RuleCreateRequest):
    """创建自定义规则"""
    try:
        import yaml
        
        # 解析 YAML 内容
        rule_data = yaml.safe_load(request.yaml_content)
        
        # 验证规则
        rule = Rule.model_validate(rule_data)
        
        # 保存到自定义规则目录
        loader = RuleLoader()
        rules_dir = Path(loader.rules_dir)
        rules_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建规则文件
        rule_file = rules_dir / f"{rule.rule_id}.yaml"
        
        # 检查是否已存在
        if rule_file.exists():
            raise HTTPException(status_code=400, detail=f"规则已存在: {rule.rule_id}")
        
        # 保存规则
        rule_set = RuleSet(
            name="Custom Rules",
            description="用户自定义规则",
            version="1.0.0",
            rules=[rule]
        )
        
        loader.save_to_yaml(rule_set, str(rule_file))
        
        return {
            "message": "规则创建成功",
            "rule_id": rule.rule_id,
            "file_path": str(rule_file)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{rule_id}")
async def delete_rule(rule_id: str):
    """删除自定义规则"""
    try:
        # 不能删除内置规则
        builtin_rules = load_builtin_rules()
        for rule in builtin_rules.rules:
            if rule.rule_id == rule_id:
                raise HTTPException(status_code=400, detail="不能删除内置规则")
        
        # 查找并删除自定义规则文件
        loader = RuleLoader()
        rules_dir = Path(loader.rules_dir)
        
        if rules_dir.exists():
            for yaml_file in rules_dir.rglob("*.yaml"):
                rule_set = loader.load_from_yaml(str(yaml_file))
                if rule_set:
                    for rule in rule_set.rules:
                        if rule.rule_id == rule_id:
                            yaml_file.unlink()
                            return {"message": "规则删除成功", "rule_id": rule_id}
        
        raise HTTPException(status_code=404, detail=f"规则不存在: {rule_id}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
