"""
WebSocket服务工厂 - 统一管理WebSocket服务的创建和依赖注入
"""
import logging
from typing import Optional

from app.core.distributed_connection_manager import DistributedConnectionManager
from app.core.redis_client import get_redis_client
from .websocket_service import WebSocketService
from app.services.broadcasting_factory import get_broadcasting_service

logger = logging.getLogger(__name__)

# 全局服务实例缓存
_websocket_service: Optional[WebSocketService] = None
_connection_manager: Optional[DistributedConnectionManager] = None


async def get_connection_manager() -> DistributedConnectionManager:
    """获取或创建分布式连接管理器实例"""
    global _connection_manager
    
    if _connection_manager is None:
        try:
            redis_client = await get_redis_client()
            _connection_manager = DistributedConnectionManager(redis_client)
            await _connection_manager.initialize()
            logger.info("分布式连接管理器初始化成功")
        except Exception as e:
            logger.error(f"初始化分布式连接管理器失败: {e}")
            raise
    
    return _connection_manager


async def create_websocket_service() -> WebSocketService:
    """
    创建WebSocket服务实例
    
    Returns:
        WebSocketService: 配置完整的WebSocket服务实例
    """
    try:
        # 获取连接管理器
        connection_manager = await get_connection_manager()
        
        # 获取广播服务
        broadcasting_service = await get_broadcasting_service()
        
        # 创建WebSocket服务
        websocket_service = WebSocketService(
            connection_manager=connection_manager,
            broadcasting_service=broadcasting_service
        )
        
        logger.info("WebSocket服务创建成功，已集成所有依赖服务")
        return websocket_service
        
    except Exception as e:
        logger.error(f"创建WebSocket服务失败: {e}")
        raise


async def get_websocket_service() -> WebSocketService:
    """
    获取WebSocket服务实例（单例模式）
    
    Returns:
        WebSocketService: WebSocket服务实例
    """
    global _websocket_service
    
    if _websocket_service is None:
        _websocket_service = await create_websocket_service()
    
    return _websocket_service


async def cleanup_websocket_services():
    """清理WebSocket服务资源（应用关闭时调用）"""
    global _websocket_service, _connection_manager
    
    try:
        if _connection_manager:
            await _connection_manager.cleanup()
            _connection_manager = None
            
        _websocket_service = None
        logger.info("WebSocket服务资源清理完成")
        
    except Exception as e:
        logger.error(f"清理WebSocket服务资源失败: {e}")


# 依赖注入函数
async def get_websocket_service_dependency() -> WebSocketService:
    """
    FastAPI依赖注入函数
    """
    return await get_websocket_service()
