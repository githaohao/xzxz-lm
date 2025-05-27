#!/usr/bin/env python3
"""
带完整日志配置的后端启动脚本
"""

import uvicorn
import sys
import os

# 添加app目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 启动小智小智后端服务 (带详细日志)")
    print("=" * 60)
    print("📋 日志配置:")
    print("   • 级别: INFO")
    print("   • 输出: 控制台 (彩色)")
    print("   • 格式: 时间 | 模块名 | 级别 | 消息")
    print("   • 访问日志: 启用")
    print("=" * 60)
    
    # 启动服务器，确保日志配置正确
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True,
        use_colors=True,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.DefaultFormatter",
                    "fmt": "%(asctime)s | %(name)-20s | %(levelprefix)s %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "access": {
                    "()": "uvicorn.logging.AccessFormatter",
                    "fmt": "%(asctime)s | ACCESS | INFO | %(client_addr)s - \"%(request_line)s\" %(status_code)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
                "access": {
                    "formatter": "access",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "uvicorn": {"handlers": ["default"], "level": "INFO"},
                "uvicorn.error": {"level": "INFO"},
                "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
                "app": {"handlers": ["default"], "level": "INFO", "propagate": False},
                "app.routes.chat": {"handlers": ["default"], "level": "INFO", "propagate": False},
                "app.services.rag_service": {"handlers": ["default"], "level": "INFO", "propagate": False},
            },
        },
        timeout_keep_alive=300,
        timeout_graceful_shutdown=30
    ) 