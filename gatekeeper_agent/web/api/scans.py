"""
扫描 API
"""

import uuid
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from gatekeeper_agent.rules.loader import load_rules
from gatekeeper_agent.core.scanner import CodeScanner
from gatekeeper_agent.models.scan import ScanResult, SourceType
from gatekeeper_agent.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# 内存存储扫描任务（生产环境应使用数据库）
scan_tasks = {}


class ScanRequest(BaseModel):
    """扫描请求"""
    target: str = "."
    scan_type: str = "staged"  # staged, diff, file, directory
    source: Optional[str] = None
    no_builtin: bool = False
    rules_dir: Optional[str] = None


class ScanTaskResponse(BaseModel):
    """扫描任务响应"""
    task_id: str
    status: str  # pending, running, completed, failed
    message: str
    created_at: str


class ScanResultResponse(BaseModel):
    """扫描结果响应"""
    task_id: str
    status: str
    result: Optional[dict] = None
    error: Optional[str] = None


def _scan_result_to_dict(result: ScanResult) -> dict:
    """将 ScanResult 转换为字典"""
    return {
        "scan_id": result.scan_id,
        "start_time": result.start_time.isoformat() if result.start_time else None,
        "end_time": result.end_time.isoformat() if result.end_time else None,
        "source_type": result.source_type.value if result.source_type else None,
        "source_info": result.source_info,
        "summary": {
            "total_files": result.summary.total_files,
            "total_lines": result.summary.total_lines,
            "fatal_count": result.summary.fatal_count,
            "error_count": result.summary.error_count,
            "warning_count": result.summary.warning_count,
            "info_count": result.summary.info_count,
            "total_violations": result.summary.total_violations,
            "blocking_violations": result.summary.blocking_violations,
        },
        "violations": [
            {
                "rule_id": v.rule_id,
                "rule_name": v.rule_name,
                "severity": v.severity,
                "category": v.category,
                "message": v.message,
                "file_path": v.file_path,
                "location": {
                    "line_number": v.location.line_number,
                    "column_start": v.location.column_start,
                    "column_end": v.location.column_end,
                    "matched_text": v.location.matched_text,
                },
                "matched_content": v.matched_content,
                "suggested_fix": v.suggested_fix,
                "require_approval": v.require_approval,
                "docs_link": v.docs_link,
            }
            for v in result.violations
        ],
        "has_blocking_violations": result.has_blocking_violations(),
    }


async def _run_scan_task(task_id: str, request: ScanRequest):
    """后台执行扫描任务"""
    try:
        scan_tasks[task_id]["status"] = "running"
        
        # 加载规则
        rule_set = load_rules(
            builtin=not request.no_builtin,
            custom_dir=request.rules_dir
        )
        
        # 创建扫描器
        scanner = CodeScanner(rule_set)
        
        # 执行扫描
        if request.scan_type == "staged":
            result = scanner.scan_staged(repo_path=request.target)
        elif request.scan_type == "diff":
            result = scanner.scan_git_diff(
                repo_path=request.target,
                target=request.target if request.target != "." else "HEAD",
                source=request.source
            )
        elif request.scan_type == "directory":
            # 扫描目录
            import os
            target_path = request.target
            if not os.path.isabs(target_path):
                # 如果是相对路径，转换为绝对路径
                target_path = os.path.abspath(target_path)
            logger.info(f"扫描目录: {target_path}")
            result = scanner.scan_directory(dir_path=target_path)
        elif request.scan_type == "file":
            # 扫描单个文件
            result = scanner.scan_file(file_path=request.target)
        else:
            raise ValueError(f"不支持的扫描类型: {request.scan_type}")
        
        # 保存结果
        result_dict = _scan_result_to_dict(result)
        scan_tasks[task_id]["status"] = "completed"
        scan_tasks[task_id]["result"] = result_dict
        scan_tasks[task_id]["completed_at"] = datetime.now().isoformat()
        # 扫描结果不自动保存，需要用户手动保存到报告中心
        
    except Exception as e:
        logger.error(f"扫描任务失败: {e}")
        scan_tasks[task_id]["status"] = "failed"
        scan_tasks[task_id]["error"] = str(e)


@router.post("", response_model=ScanTaskResponse)
async def create_scan(
    request: ScanRequest,
    background_tasks: BackgroundTasks
):
    """创建扫描任务"""
    try:
        task_id = str(uuid.uuid4())
        
        scan_tasks[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "request": request.dict(),
        }
        
        # 后台执行扫描
        background_tasks.add_task(_run_scan_task, task_id, request)
        
        return ScanTaskResponse(
            task_id=task_id,
            status="pending",
            message="扫描任务已创建",
            created_at=scan_tasks[task_id]["created_at"]
        )
    except Exception as e:
        logger.error(f"创建扫描任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=List[ScanTaskResponse])
async def list_scan_tasks(
    limit: int = 10,
    status: Optional[str] = None
):
    """获取扫描任务列表"""
    try:
        tasks = []
        for task_id, task in sorted(
            scan_tasks.items(),
            key=lambda x: x[1].get("created_at", ""),
            reverse=True
        )[:limit]:
            if status and task.get("status") != status:
                continue
            tasks.append(ScanTaskResponse(
                task_id=task_id,
                status=task.get("status", "unknown"),
                message="",
                created_at=task.get("created_at", "")
            ))
        return tasks
    except Exception as e:
        logger.error(f"获取扫描任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks/{task_id}", response_model=ScanResultResponse)
async def get_scan_result(task_id: str):
    """获取扫描结果"""
    try:
        if task_id not in scan_tasks:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
        
        task = scan_tasks[task_id]
        
        return ScanResultResponse(
            task_id=task_id,
            status=task.get("status", "unknown"),
            result=task.get("result"),
            error=task.get("error")
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取扫描结果失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/tasks/{task_id}")
async def delete_scan_task(task_id: str):
    """删除扫描任务"""
    try:
        if task_id not in scan_tasks:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
        
        del scan_tasks[task_id]
        return {"message": "任务已删除", "task_id": task_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除扫描任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/{task_id}/save-report")
async def save_scan_report(task_id: str):
    """将扫描结果保存为报告"""
    try:
        if task_id not in scan_tasks:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
        
        task = scan_tasks[task_id]
        if task.get("status") != "completed":
            raise HTTPException(status_code=400, detail="扫描任务尚未完成")
        
        result = task.get("result")
        if not result:
            raise HTTPException(status_code=400, detail="扫描结果为空")
        
        # 导入报告模块
        from gatekeeper_agent.web.api.reports import reports_db, _generate_report_id
        
        report_id = _generate_report_id()
        reports_db[report_id] = {
            "report_id": report_id,
            "scan_id": result.get("scan_id", ""),
            "created_at": datetime.now().isoformat(),
            "source_type": result.get("source_type", ""),
            "total_files": result.get("summary", {}).get("total_files", 0),
            "total_violations": result.get("summary", {}).get("total_violations", 0),
            "fatal_count": result.get("summary", {}).get("fatal_count", 0),
            "error_count": result.get("summary", {}).get("error_count", 0),
            "warning_count": result.get("summary", {}).get("warning_count", 0),
            "info_count": result.get("summary", {}).get("info_count", 0),
            "has_blocking": result.get("has_blocking_violations", False),
            "violations": result.get("violations", []),
        }
        
        return {
            "message": "报告已保存",
            "report_id": report_id,
            "task_id": task_id
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"保存报告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
