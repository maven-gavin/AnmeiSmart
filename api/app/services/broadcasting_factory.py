"""
广播服务工厂 - 统一管理BroadcastingService的创建和依赖注入
"""
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.core.distributed_connection_manager import DistributedConnectionManager
from app.core.redis_client import get_redis_client
from app.services.broadcasting_service import BroadcastingService
from app.services.notification_service import NotificationService, get_notification_service

logger = logging.getLogger(__name__)

# 全局服务实例缓存
_broadcasting_service: Optional[BroadcastingService] = None
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


async def create_broadcasting_service(db: Session = None, notification_service: NotificationService = None) -> BroadcastingService:
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


async def get_broadcasting_service(db: Session = None) -> BroadcastingService:
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
    global _broadcasting_service, _connection_manager
    
    try:
        if _connection_manager:
            await _connection_manager.cleanup()
            _connection_manager = None
            
        _broadcasting_service = None
        logger.info("广播服务资源清理完成")
        
    except Exception as e:
        logger.error(f"清理广播服务资源失败: {e}")


# 依赖注入函数
async def get_broadcasting_service_dependency(db: Session = None) -> BroadcastingService:
    """
    FastAPI依赖注入函数
    """
    return await get_broadcasting_service(db) 