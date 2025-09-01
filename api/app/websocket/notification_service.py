"""
通知推送服务 - 处理离线推送通知
当前使用日志记录服务，未来可扩展为真实推送服务

TODO 备注：
- Firebase FCM推送服务集成
- Apple APNs推送服务集成  
- 第三方推送服务集成（极光推送、友盟等）
- 用户推送偏好设置
- 推送模板管理
- 推送统计和监控
"""
import logging
import os
from typing import Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod
from enum import Enum
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class DeviceType(Enum):
    """设备类型枚举"""
    MOBILE = "mobile"
    DESKTOP = "desktop"
    TABLET = "tablet"
    WEB = "web"


class PushPriority(Enum):
    """推送优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationProvider(ABC):
    """推送服务提供商抽象基类"""
    
    @abstractmethod
    async def send_notification(
        self, 
        user_id: str, 
        title: str, 
        body: str, 
        data: Optional[Dict[str, Any]] = None,
        device_type: Optional[DeviceType] = None,
        priority: PushPriority = PushPriority.NORMAL
    ) -> bool:
        """发送推送通知"""
        pass


class LoggingNotificationProvider(NotificationProvider):
    """日志记录推送服务（用于开发和测试）"""
    
    async def send_notification(
        self, 
        user_id: str, 
        title: str, 
        body: str, 
        data: Optional[Dict[str, Any]] = None,
        device_type: Optional[DeviceType] = None,
        priority: PushPriority = PushPriority.NORMAL
    ) -> bool:
        """发送推送通知（仅记录日志）"""
        try:
            device_info = f" [{device_type.value}]" if device_type else ""
            priority_info = f" [优先级: {priority.value}]"
            data_info = f" [数据: {data}]" if data else ""
            
            logger.info(f"📱 推送通知{device_info}{priority_info}: {user_id}")
            logger.info(f"   标题: {title}")
            logger.info(f"   内容: {body}")
            if data_info:
                logger.info(f"   {data_info}")
            logger.info("   ─" * 30)  # 分隔线，便于阅读
            
            return True
            
        except Exception as e:
            logger.error(f"发送推送通知失败: {e}")
            return False


class FirebaseNotificationProvider(NotificationProvider):
    """Firebase FCM推送服务（待实现）"""
    
    def __init__(self, fcm_credentials: Dict[str, Any]):
        # TODO: 初始化Firebase FCM客户端
        # self.fcm_client = initialize_fcm_client(fcm_credentials)
        logger.warning("Firebase FCM推送服务尚未实现")
    
    async def send_notification(
        self, 
        user_id: str, 
        title: str, 
        body: str, 
        data: Optional[Dict[str, Any]] = None,
        device_type: Optional[DeviceType] = None,
        priority: PushPriority = PushPriority.NORMAL
    ) -> bool:
        """发送Firebase FCM推送通知"""
        try:
            # TODO: 实现Firebase FCM推送逻辑
            # 1. 根据user_id获取设备tokens
            # 2. 构建FCM消息
            # 3. 发送推送
            # 4. 处理发送结果
            
            logger.warning(f"Firebase FCM推送尚未实现: user_id={user_id}")
            return False
            
        except Exception as e:
            logger.error(f"Firebase FCM推送失败: {e}")
            return False


class NotificationService:
    """
    通知推送服务主类
    """
    
    def __init__(self, provider: Optional[NotificationProvider] = None):
        """
        初始化通知服务
        
        Args:
            provider: 推送服务提供商，默认使用日志记录服务
        """
        self.provider = provider or LoggingNotificationProvider()
        logger.info(f"通知服务已初始化，使用提供商: {type(self.provider).__name__}")
    
    async def send_push_notification(
        self, 
        user_id: str, 
        notification_data: Dict[str, Any],
        device_type: Optional[str] = None
    ) -> bool:
        """
        发送推送通知
        
        Args:
            user_id: 目标用户ID
            notification_data: 通知数据，包含title、body等
            device_type: 设备类型字符串
        
        Returns:
            bool: 发送是否成功
        """
        try:
            title = notification_data.get("title", "新消息")
            body = notification_data.get("body", "")
            data = notification_data.get("data", {})
            priority_str = notification_data.get("priority", "normal")
            
            # 转换设备类型
            device_enum = None
            if device_type:
                try:
                    device_enum = DeviceType(device_type.lower())
                except ValueError:
                    logger.warning(f"未知设备类型: {device_type}")
            
            # 转换优先级
            try:
                priority_enum = PushPriority(priority_str.lower())
            except ValueError:
                priority_enum = PushPriority.NORMAL
            
            # 发送推送
            success = await self.provider.send_notification(
                user_id=user_id,
                title=title,
                body=body,
                data=data,
                device_type=device_enum,
                priority=priority_enum
            )
            
            if success:
                logger.debug(f"推送通知发送成功: user_id={user_id}")
            else:
                logger.warning(f"推送通知发送失败: user_id={user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"发送推送通知异常: user_id={user_id}, error={e}")
            return False
    
    async def send_batch_notifications(
        self, 
        notifications: List[Dict[str, Any]]
    ) -> Dict[str, bool]:
        """
        批量发送推送通知
        
        Args:
            notifications: 通知列表，每个包含user_id和notification_data
        
        Returns:
            Dict[str, bool]: 用户ID -> 发送结果的映射
        """
        results = {}
        
        for notification in notifications:
            user_id = notification.get("user_id")
            notification_data = notification.get("notification_data", {})
            device_type = notification.get("device_type")
            
            if user_id:
                result = await self.send_push_notification(
                    user_id=user_id,
                    notification_data=notification_data,
                    device_type=device_type
                )
                results[user_id] = result
            else:
                logger.warning("批量通知中缺少user_id")
        
        logger.info(f"批量推送完成: 总数={len(notifications)}, 成功={sum(results.values())}")
        return results


# 全局通知服务实例
_notification_service: Optional[NotificationService] = None


def get_notification_service() -> NotificationService:
    """获取通知服务实例（单例模式）"""
    global _notification_service
    
    if _notification_service is None:
        _notification_service = NotificationService()
    
    return _notification_service


def create_notification_service(provider: Optional[NotificationProvider] = None) -> NotificationService:
    """创建通知服务实例"""
    return NotificationService(provider)


# 便捷函数
async def send_push_notification(
    user_id: str, 
    title: str, 
    body: str, 
    data: Optional[Dict[str, Any]] = None,
    device_type: Optional[str] = None,
    priority: str = "normal"
) -> bool:
    """便捷函数：发送推送通知"""
    service = get_notification_service()
    
    notification_data = {
        "title": title,
        "body": body,
        "data": data or {},
        "priority": priority
    }
    
    return await service.send_push_notification(
        user_id=user_id,
        notification_data=notification_data,
        device_type=device_type
    ) 