"""
Web 界面配置
"""

import os
from pathlib import Path

# 默认配置
DEFAULT_CONFIG = {
    # 报告保存路径
    "report_save_path": os.path.expanduser("~/.gatekeeper/reports"),
    
    # 是否自动保存报告
    "auto_save_report": False,
    
    # 默认报告格式
    "default_report_format": "html",
    
    # 服务器配置
    "host": "127.0.0.1",
    "port": 8080,
    
    # 前端配置
    "frontend_dist_path": None,  # 自动检测
}


def get_config():
    """获取配置"""
    config = DEFAULT_CONFIG.copy()
    
    # 从环境变量读取配置
    if os.environ.get("GATEKEEPER_REPORT_PATH"):
        config["report_save_path"] = os.environ.get("GATEKEEPER_REPORT_PATH")
    
    if os.environ.get("GATEKEEPER_AUTO_SAVE"):
        config["auto_save_report"] = os.environ.get("GATEKEEPER_AUTO_SAVE").lower() == "true"
    
    if os.environ.get("GATEKEEPER_WEB_HOST"):
        config["host"] = os.environ.get("GATEKEEPER_WEB_HOST")
    
    if os.environ.get("GATEKEEPER_WEB_PORT"):
        config["port"] = int(os.environ.get("GATEKEEPER_WEB_PORT"))
    
    # 确保报告保存目录存在
    report_path = Path(config["report_save_path"])
    report_path.mkdir(parents=True, exist_ok=True)
    
    return config


def get_report_save_path() -> str:
    """获取报告保存路径"""
    config = get_config()
    return config["report_save_path"]
