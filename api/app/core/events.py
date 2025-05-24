"""
事件系统 - 用于WebSocket基础设施与业务逻辑的解耦
"""
from typing import Dict, List, Callable, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)


@dataclass
class Event:
    """事件基类"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str = "unknown"
    conversation_id: str = None
    user_id: str = None


@dataclass
class MessageEvent(Event):
    """消息事件"""
    pass


@dataclass
class UserEvent(Event):
    """用户事件（连接、断开等）"""
    pass


@dataclass
class SystemEvent(Event):
    """系统事件"""
    pass


class EventBus:
    """事件总线 - 管理事件的发布和订阅"""
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._async_handlers: Dict[str, List[Callable]] = {}
    
    def subscribe(self, event_type: str, handler: Callable):
        """订阅同步事件处理器"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"订阅事件处理器: {event_type} -> {handler.__name__}")
    
    def subscribe_async(self, event_type: str, handler: Callable):
        """订阅异步事件处理器"""
        if event_type not in self._async_handlers:
            self._async_handlers[event_type] = []
        self._async_handlers[event_type].append(handler)
        logger.debug(f"订阅异步事件处理器: {event_type} -> {handler.__name__}")
    
    def unsubscribe(self, event_type: str, handler: Callable):
        """取消订阅事件处理器"""
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
        if event_type in self._async_handlers and handler in self._async_handlers[event_type]:
            self._async_handlers[event_type].remove(handler)
    
    def publish(self, event: Event):
        """发布同步事件"""
        handlers = self._handlers.get(event.type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"事件处理器执行失败: {handler.__name__}, 错误: {e}")
    
    async def publish_async(self, event: Event):
        """发布异步事件"""
        # 处理同步事件处理器
        self.publish(event)
        
        # 处理异步事件处理器
        async_handlers = self._async_handlers.get(event.type, [])
        if async_handlers:
            tasks = []
            for handler in async_handlers:
                try:
                    task = asyncio.create_task(handler(event))
                    tasks.append(task)
                except Exception as e:
                    logger.error(f"创建异步事件处理任务失败: {handler.__name__}, 错误: {e}")
            
            if tasks:
                try:
                    await asyncio.gather(*tasks, return_exceptions=True)
                except Exception as e:
                    logger.error(f"异步事件处理失败: {e}")


# 全局事件总线实例
event_bus = EventBus()


# 事件类型常量
class EventTypes:
    # WebSocket事件
    WS_CONNECT = "ws_connect"
    WS_DISCONNECT = "ws_disconnect"
    WS_MESSAGE = "ws_message"
    
    # 聊天事件
    CHAT_MESSAGE_RECEIVED = "chat_message_received"
    CHAT_MESSAGE_SENT = "chat_message_sent"
    CHAT_TYPING = "chat_typing"
    CHAT_READ = "chat_read"
    
    # AI事件
    AI_RESPONSE_REQUESTED = "ai_response_requested"
    AI_RESPONSE_GENERATED = "ai_response_generated"
    AI_RESPONSE_FAILED = "ai_response_failed"
    
    # 系统事件
    SYSTEM_ERROR = "system_error"
    SYSTEM_NOTIFICATION = "system_notification"


def create_message_event(
    conversation_id: str,
    user_id: str,
    content: str,
    message_type: str = "text",
    sender_type: str = "user",
    **kwargs
) -> MessageEvent:
    """创建消息事件的便捷函数"""
    return MessageEvent(
        type=EventTypes.CHAT_MESSAGE_RECEIVED,
        data={
            "content": content,
            "message_type": message_type,
            "sender_type": sender_type,
            **kwargs
        },
        timestamp=datetime.now(),
        conversation_id=conversation_id,
        user_id=user_id,
        source="websocket"
    )


def create_user_event(
    event_type: str,
    user_id: str,
    conversation_id: str = None,
    **kwargs
) -> UserEvent:
    """创建用户事件的便捷函数"""
    return UserEvent(
        type=event_type,
        data=kwargs,
        timestamp=datetime.now(),
        conversation_id=conversation_id,
        user_id=user_id,
        source="websocket"
    )


def create_system_event(
    event_type: str,
    message: str,
    conversation_id: str = None,
    **kwargs
) -> SystemEvent:
    """创建系统事件的便捷函数"""
    return SystemEvent(
        type=event_type,
        data={
            "message": message,
            **kwargs
        },
        timestamp=datetime.now(),
        conversation_id=conversation_id,
        source="system"
    ) 