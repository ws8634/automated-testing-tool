"""
统计 API
"""

from typing import Dict, List
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from gatekeeper_agent.rules.loader import load_rules, load_builtin_rules
from gatekeeper_agent.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


class StatsResponse(BaseModel):
    """统计响应"""
    total_rules: int
    builtin_rules: int
    custom_rules: int
    rules_by_category: Dict[str, int]
    rules_by_severity: Dict[str, int]


class TrendData(BaseModel):
    """趋势数据"""
    date: str
    scan_count: int
    violation_count: int
    blocking_count: int


class TrendResponse(BaseModel):
    """趋势响应"""
    trends: List[TrendData]


@router.get("", response_model=StatsResponse)
async def get_stats():
    """获取统计信息"""
    try:
        # 加载规则
        builtin_rules = load_builtin_rules()
        all_rules = load_rules()
        
        # 统计分类
        categories = {}
        severities = {}
        
        for rule in all_rules.rules:
            cat = rule.category.value
            categories[cat] = categories.get(cat, 0) + 1
            
            sev = rule.severity.value
            severities[sev] = severities.get(sev, 0) + 1
        
        return StatsResponse(
            total_rules=len(all_rules.rules),
            builtin_rules=len(builtin_rules.rules),
            custom_rules=len(all_rules.rules) - len(builtin_rules.rules),
            rules_by_category=categories,
            rules_by_severity=severities,
        )
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/trends", response_model=TrendResponse)
async def get_trends(days: int = 7):
    """获取扫描趋势"""
    try:
        # 生成模拟趋势数据（实际应从数据库查询）
        trends = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
            # 这里应该查询实际的扫描历史
            trends.append(TrendData(
                date=date,
                scan_count=0,  # 从数据库查询
                violation_count=0,
                blocking_count=0,
            ))
        
        return TrendResponse(trends=trends)
    except Exception as e:
        logger.error(f"获取趋势数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dashboard")
async def get_dashboard():
    """获取 Dashboard 数据"""
    try:
        # 规则统计
        builtin_rules = load_builtin_rules()
        all_rules = load_rules()
        
        # 分类统计
        category_stats = {}
        for rule in all_rules.rules:
            cat = rule.category.value
            category_stats[cat] = category_stats.get(cat, 0) + 1
        
        # 风险等级统计
        severity_stats = {}
        for rule in all_rules.rules:
            sev = rule.severity.value
            severity_stats[sev] = severity_stats.get(sev, 0) + 1
        
        return {
            "rules": {
                "total": len(all_rules.rules),
                "builtin": len(builtin_rules.rules),
                "custom": len(all_rules.rules) - len(builtin_rules.rules),
                "by_category": category_stats,
                "by_severity": severity_stats,
            },
            "scans": {
                "total_scans": 0,  # 从数据库查询
                "total_violations": 0,
                "blocking_violations": 0,
                "last_scan": None,
            },
            "recent_violations": [],  # 最近的违规项
        }
    except Exception as e:
        logger.error(f"获取 Dashboard 数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
