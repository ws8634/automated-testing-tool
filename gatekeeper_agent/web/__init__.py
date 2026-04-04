"""
Web 管理界面模块

提供规则管理和报告查看的 Web 界面
"""

from gatekeeper_agent.web.server import create_app, start_server

__all__ = ["create_app", "start_server"]
