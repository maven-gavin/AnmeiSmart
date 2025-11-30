"""
广播服务工厂 - 统一管理BroadcastingService的创建和依赖注入
"""
import logging
from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.core.websocket.websocket_coordinator import WebSocketCoordinator
from app.core.redis_client import get_redis_client
from .broadcasting_service import BroadcastingService
from .notification_service import NotificationService, get_notification_service

logger = logging.getLogger(__name__)

# 全局服务实例缓存
_broadcasting_service: Optional[BroadcastingService] = None

# 注意：连接管理器应该从 websocket_factory 获取，确保使用同一个实例
async def get_connection_manager() -> WebSocketCoordinator:
    """获取WebSocket协调器实例（从websocket_factory获取，确保单例）"""
    from app.websocket.websocket_factory import get_connection_manager as get_ws_connection_manager
    return await get_ws_connection_manager()


async def create_broadcasting_service(db: Optional[Session] = None, notification_service: Optional[NotificationService] = None) -> BroadcastingService:
    """
    创建广播服务实例
    
    Args:
        db: 数据库会话（可选，如果不提供则不能查询会话参与者）
        notification_service: 通知推送服务（可选，默认使用日志记录服务）
    
    Returns:
        BroadcastingService: 配置完整的广播服务实例
    """
    try:
        # 获取连接管理器
        connection_manager = await get_connection_manager()
        
        # 获取通知服务
        if notification_service is None:
            notification_service = get_notification_service()
        
        # 创建广播服务
        broadcasting_service = BroadcastingService(
            connection_manager=connection_manager,
            db=db,
            notification_service=notification_service
        )
        
        logger.info("广播服务创建成功，已集成所有依赖服务")
        return broadcasting_service
        
    except Exception as e:
        logger.error(f"创建广播服务失败: {e}")
        raise


async def get_broadcasting_service(db: Optional[Session] = None) -> BroadcastingService:
    """
    获取广播服务实例（单例模式）
    
    Args:
        db: 数据库会话（可选）
    
    Returns:
        BroadcastingService: 广播服务实例
    """
    global _broadcasting_service
    
    # 每次都创建新实例以支持不同的数据库会话
    # 连接管理器是共享的，但数据库会话是独立的
    return await create_broadcasting_service(db)


async def cleanup_broadcasting_services():
    """清理广播服务资源（应用关闭时调用）"""
    global _broadcasting_service
    
    try:
        # 注意：连接管理器由 websocket_factory 管理，这里不需要清理
        _broadcasting_service = None
        logger.info("广播服务资源清理完成")
        
    except Exception as e:
        logger.error(f"清理广播服务资源失败: {e}")


# 依赖注入函数
async def get_broadcasting_service_dependency(
    db: Optional[Session] = Depends(get_db)
) -> BroadcastingService:
    """
    FastAPI依赖注入函数
    """
    return await get_broadcasting_service(db) 