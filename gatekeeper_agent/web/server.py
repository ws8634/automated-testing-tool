"""
FastAPI Web 服务器
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn

from gatekeeper_agent.web.api import rules, scans, reports, stats
from gatekeeper_agent.utils.logger import get_logger

logger = get_logger(__name__)


def create_app(static_dir: Optional[str] = None) -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="Gatekeeper Web",
        description="Gatekeeper Agent Web 管理界面",
        version="0.1.0",
    )
    
    # CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册 API 路由
    app.include_router(rules.router, prefix="/api/rules", tags=["rules"])
    app.include_router(scans.router, prefix="/api/scans", tags=["scans"])
    app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
    app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
    
    # 静态文件服务
    if static_dir and Path(static_dir).exists():
        app.mount("/assets", StaticFiles(directory=f"{static_dir}/assets"), name="assets")
        
        @app.get("/")
        async def root():
            return FileResponse(f"{static_dir}/index.html")
        
        @app.get("/{path:path}")
        async def catch_all(path: str):
            file_path = Path(static_dir) / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(f"{static_dir}/index.html")
    
    @app.get("/api/health")
    async def health_check():
        return {"status": "ok", "version": "0.1.0"}
    
    return app


def start_server(
    port: int = 8080,
    host: str = "127.0.0.1",
    static_dir: Optional[str] = None,
    reload: bool = False
) -> None:
    """启动 Web 服务器"""
    
    # 查找前端构建产物目录
    if static_dir is None:
        possible_paths = [
            Path(__file__).parent / "frontend" / "dist",
            Path.cwd() / "web" / "dist",
            Path.cwd() / "gatekeeper_agent" / "web" / "frontend" / "dist",
        ]
        for path in possible_paths:
            if path.exists():
                static_dir = str(path)
                break
    
    app = create_app(static_dir)
    
    logger.info(f"启动 Gatekeeper Web 服务器: http://{host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
