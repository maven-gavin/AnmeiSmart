"""
事件系统 - 用于WebSocket基础设施与业务逻辑的解耦

该模块提供了基于发布-订阅模式的事件系统，支持同步和异步事件处理。
主要组件包括：
- Event基类及子类：定义事件数据结构
- EventBus：事件总线，管理事件发布和订阅
- 便捷函数：简化事件创建
"""
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging
from contextlib import suppress
import threading

logger = logging.getLogger(__name__)

# 配置常量
MAX_HANDLERS_PER_EVENT = 100  # 每个事件类型的最大处理器数量
MAX_EVENT_DATA_SIZE = 1024 * 1024  # 事件数据最大大小 (1MB)


@dataclass
class Event:
    """事件基类"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None
    
    def __post_init__(self) -> None:
        """事件创建后的验证"""
        if not self.type or not isinstance(self.type, str):
            raise ValueError("事件类型必须是非空字符串")
        
        if not isinstance(self.data, dict):
            raise ValueError("事件数据必须是字典类型")
        
        # 检查数据大小
        data_size = len(str(self.data))
        if data_size > MAX_EVENT_DATA_SIZE:
            raise ValueError(f"事件数据过大: {data_size} bytes > {MAX_EVENT_DATA_SIZE} bytes")


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
    
    def __init__(self) -> None:
        self._handlers: Dict[str, List[Callable[[Event], None]]] = {}
        self._async_handlers: Dict[str, List[Callable[[Event], Any]]] = {}
        self._lock = threading.RLock()  # 可重入锁，支持同一线程多次获取
    
    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """订阅同步事件处理器
        
        Args:
            event_type: 事件类型
            handler: 同步事件处理函数
            
        Raises:
            ValueError: 当处理器数量超过限制时
        """
        if not event_type or not handler:
            raise ValueError("事件类型和处理器不能为空")
        
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            
            if len(self._handlers[event_type]) >= MAX_HANDLERS_PER_EVENT:
                raise ValueError(f"事件类型 {event_type} 的处理器数量已达到上限: {MAX_HANDLERS_PER_EVENT}")
            
            self._handlers[event_type].append(handler)
            logger.debug(f"订阅事件处理器: {event_type} -> {handler.__name__}")
    
    def subscribe_async(self, event_type: str, handler: Callable[[Event], Any]) -> None:
        """订阅异步事件处理器
        
        Args:
            event_type: 事件类型
            handler: 异步事件处理函数
            
        Raises:
            ValueError: 当处理器数量超过限制时
        """
        if not event_type or not handler:
            raise ValueError("事件类型和处理器不能为空")
        
        with self._lock:
            if event_type not in self._async_handlers:
                self._async_handlers[event_type] = []
            
            if len(self._async_handlers[event_type]) >= MAX_HANDLERS_PER_EVENT:
                raise ValueError(f"事件类型 {event_type} 的异步处理器数量已达到上限: {MAX_HANDLERS_PER_EVENT}")
            
            self._async_handlers[event_type].append(handler)
            logger.debug(f"订阅异步事件处理器: {event_type} -> {handler.__name__}")
    
    def unsubscribe(self, event_type: str, handler: Callable) -> bool:
        """取消订阅事件处理器
        
        Args:
            event_type: 事件类型
            handler: 要取消的事件处理函数
            
        Returns:
            bool: 是否成功取消订阅
        """
        if not event_type or not handler:
            return False
        
        with self._lock:
            removed = False
            with suppress(ValueError):
                if event_type in self._handlers:
                    self._handlers[event_type].remove(handler)
                    removed = True
                if event_type in self._async_handlers:
                    self._async_handlers[event_type].remove(handler)
                    removed = True
            
            if removed:
                logger.debug(f"取消订阅事件处理器: {event_type} -> {handler.__name__}")
            
            return removed
    
    def publish(self, event: Event) -> None:
        """发布同步事件
        
        Args:
            event: 要发布的事件
        """
        if not event:
            logger.warning("尝试发布空事件")
            return
        
        # 创建处理器列表的快照，避免在迭代时修改
        with self._lock:
            handlers = self._handlers.get(event.type, [])[:]
        
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"事件处理器执行失败: {handler.__name__}, 错误: {e}", exc_info=True)
    
    async def publish_async(self, event: Event) -> None:
        """发布异步事件
        
        Args:
            event: 要发布的事件
        """
        if not event:
            logger.warning("尝试发布空事件")
            return
        
        # 处理同步事件处理器
        self.publish(event)
        
        # 创建异步处理器列表的快照
        with self._lock:
            async_handlers = self._async_handlers.get(event.type, [])[:]
        
        if not async_handlers:
            return
            
        tasks = []
        for handler in async_handlers:
            try:
                task = asyncio.create_task(handler(event))
                tasks.append(task)
            except Exception as e:
                logger.error(f"创建异步事件处理任务失败: {handler.__name__}, 错误: {e}", exc_info=True)
        
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                logger.error(f"异步事件处理失败: {e}", exc_info=True)
    
    def get_handler_count(self, event_type: str) -> int:
        """获取指定事件类型的处理器数量
        
        Args:
            event_type: 事件类型
            
        Returns:
            int: 处理器总数（同步+异步）
        """
        with self._lock:
            sync_count = len(self._handlers.get(event_type, []))
            async_count = len(self._async_handlers.get(event_type, []))
            return sync_count + async_count
    
    def clear_handlers(self, event_type: Optional[str] = None) -> None:
        """清除事件处理器
        
        Args:
            event_type: 事件类型，如果为None则清除所有
        """
        with self._lock:
            if event_type is None:
                self._handlers.clear()
                self._async_handlers.clear()
                logger.info("清除所有事件处理器")
            else:
                self._handlers.pop(event_type, None)
                self._async_handlers.pop(event_type, None)
                logger.info(f"清除事件类型 {event_type} 的所有处理器")


# 全局事件总线实例
event_bus = EventBus()


# 事件类型常量
class EventTypes:
    """事件类型常量定义"""
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
    """创建消息事件的便捷函数
    
    Args:
        conversation_id: 会话ID
        user_id: 用户ID
        content: 消息内容
        message_type: 消息类型，默认为"text"
        sender_type: 发送者类型，默认为"user"
        **kwargs: 其他数据字段
        
    Returns:
        MessageEvent: 消息事件实例
        
    Raises:
        ValueError: 当必需参数为空或数据过大时
    """
    if not conversation_id or not user_id or not content:
        raise ValueError("conversation_id、user_id和content不能为空")
    
    return MessageEvent(
        type=EventTypes.CHAT_MESSAGE_SENT,
        data={
            "content": content,
            "message_type": message_type,
            "sender_type": sender_type,
            **kwargs
        },
        conversation_id=conversation_id,
        user_id=user_id,
        source="websocket"
    )


def create_user_event(
    event_type: str,
    user_id: str,
    conversation_id: Optional[str] = None,
    **kwargs
) -> UserEvent:
    """创建用户事件的便捷函数
    
    Args:
        event_type: 事件类型
        user_id: 用户ID
        conversation_id: 会话ID，可选
        **kwargs: 其他数据字段
        
    Returns:
        UserEvent: 用户事件实例
        
    Raises:
        ValueError: 当必需参数为空时
    """
    if not event_type or not user_id:
        raise ValueError("event_type和user_id不能为空")
    
    return UserEvent(
        type=event_type,
        data=kwargs,
        conversation_id=conversation_id,
        user_id=user_id,
        source="websocket"
    )


def create_system_event(
    event_type: str,
    message: str,
    conversation_id: Optional[str] = None,
    **kwargs
) -> SystemEvent:
    """创建系统事件的便捷函数
    
    Args:
        event_type: 事件类型
        message: 系统消息
        conversation_id: 会话ID，可选
        **kwargs: 其他数据字段
        
    Returns:
        SystemEvent: 系统事件实例
        
    Raises:
        ValueError: 当必需参数为空时
    """
    if not event_type or not message:
        raise ValueError("event_type和message不能为空")
    
    return SystemEvent(
        type=event_type,
        data={
            "message": message,
            **kwargs
        },
        conversation_id=conversation_id,
        source="system"
    ) 