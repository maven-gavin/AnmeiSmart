"""
WebSocket生命周期管理 - 处理应用启动和关闭事件
"""
import logging
from fastapi import FastAPI

from app.services.websocket import cleanup_websocket_services
from app.services.broadcasting_factory import cleanup_broadcasting_services

logger = logging.getLogger(__name__)


def setup_websocket_lifecycle(app: FastAPI):
    """设置WebSocket生命周期管理"""
    
    @app.on_event("startup")
    async def startup_websocket_services():
        """应用启动时初始化WebSocket服务"""
        try:
            # WebSocket服务会在首次使用时自动初始化
            # 这里可以添加其他启动逻辑
            logger.info("WebSocket服务生命周期管理已设置")
        except Exception as e:
            logger.error(f"WebSocket服务启动失败: {e}")
            raise
    
    @app.on_event("shutdown")
    async def shutdown_websocket_services():
        """应用关闭时清理WebSocket服务"""
        try:
            # 清理WebSocket服务
            await cleanup_websocket_services()
            
            # 清理广播服务
            await cleanup_broadcasting_services()
            
            logger.info("WebSocket服务清理完成")
        except Exception as e:
            logger.error(f"WebSocket服务清理失败: {e}")
