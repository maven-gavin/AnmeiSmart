"""
消息路由器 - 负责消息路由、序列化和验证
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional, Set
from datetime import datetime
from fastapi import WebSocket

from app.core.redis_client import RedisClient

logger = logging.getLogger(__name__)


class MessageTooLarge(Exception):
    """消息过大异常"""
    pass


class MessageRateLimitExceeded(Exception):
    """消息频率超限异常"""
    pass


class MessageRouter:
    """消息路由器 - 专注于消息路由、序列化和验证"""
    
    def __init__(self, redis_client: RedisClient, 
                 max_message_size: int = 1024 * 1024,  # 1MB
                 rate_limit_window: int = 60,  # 秒
                 rate_limit_max_messages: int = 100):
        self.redis_client = redis_client
        self.max_message_size = max_message_size
        self.rate_limit_window = rate_limit_window
        self.rate_limit_max_messages = rate_limit_max_messages
        
        # 消息频率限制跟踪
        self.message_counters: Dict[str, Dict[str, int]] = {}  # user_id -> {timestamp: count}
        
        # Redis频道配置
        self.broadcast_channel = "ws:broadcast"
        self.presence_channel = "ws:presence"
        
        # 实例标识
        self.instance_id = f"router_{datetime.now().timestamp()}"
    
    def _make_serializable(self, obj: Any) -> Any:
        """确保对象是可序列化的"""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif hasattr(obj, 'isoformat'):  # 处理其他可能有isoformat方法的对象
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):  # 处理自定义对象
            return str(obj)
        else:
            return obj
    
    def _validate_message_size(self, payload: Dict[str, Any]) -> None:
        """验证消息大小"""
        message_size = len(json.dumps(payload))
        if message_size > self.max_message_size:
            raise MessageTooLarge(
                f"消息大小 {message_size} 超过限制 {self.max_message_size}"
            )
    
    def _check_rate_limit(self, user_id: str) -> None:
        """检查消息频率限制"""
        current_time = int(datetime.now().timestamp())
        window_start = current_time - self.rate_limit_window
        
        # 清理过期的计数器
        if user_id in self.message_counters:
            self.message_counters[user_id] = {
                timestamp: count 
                for timestamp, count in self.message_counters[user_id].items()
                if int(timestamp) > window_start
            }
        
        # 计算当前窗口内的消息数量
        current_count = sum(
            self.message_counters.get(user_id, {}).values()
        )
        
        if current_count >= self.rate_limit_max_messages:
            raise MessageRateLimitExceeded(
                f"用户 {user_id} 消息频率超限: {current_count}/{self.rate_limit_max_messages}"
            )
        
        # 更新计数器
        if user_id not in self.message_counters:
            self.message_counters[user_id] = {}
        if str(current_time) not in self.message_counters[user_id]:
            self.message_counters[user_id][str(current_time)] = 0
        self.message_counters[user_id][str(current_time)] += 1
    
    async def send_to_user(self, user_id: str, payload: Dict[str, Any]) -> None:
        """向指定用户发送消息"""
        try:
            # 验证消息大小
            self._validate_message_size(payload)
            
            # 检查频率限制
            self._check_rate_limit(user_id)
            
            # 序列化消息
            serializable_payload = self._make_serializable(payload)
            
            message = {
                "target_user_id": user_id,
                "payload": serializable_payload,
                "instance_id": self.instance_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # 发布到Redis
            await self.redis_client.publish(self.broadcast_channel, json.dumps(message))
            logger.debug(f"消息已发布到Redis: user_id={user_id}")
            
        except Exception as e:
            logger.error(f"发送消息到用户失败: {e}")
            raise
    
    async def send_to_device(self, connection_id: str, payload: Dict[str, Any]) -> None:
        """向指定设备发送消息"""
        try:
            # 验证消息大小
            self._validate_message_size(payload)
            
            message = {
                "target_connection_id": connection_id,
                "payload": payload,
                "instance_id": self.instance_id,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis_client.publish(self.broadcast_channel, json.dumps(message))
            logger.debug(f"消息已发布到Redis（按设备）: connection_id={connection_id}")
            
        except Exception as e:
            logger.error(f"发送消息到设备失败: {e}")
            raise
    
    async def send_to_device_type(self, user_id: str, device_type: str, payload: Dict[str, Any]) -> None:
        """向用户的特定类型设备发送消息"""
        try:
            # 验证消息大小
            self._validate_message_size(payload)
            
            # 检查频率限制
            self._check_rate_limit(user_id)
            
            message = {
                "target_user_id": user_id,
                "target_device_type": device_type,
                "payload": payload,
                "instance_id": self.instance_id,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis_client.publish(self.broadcast_channel, json.dumps(message))
            logger.debug(f"消息已发布到Redis（按设备类型）: user_id={user_id}, device_type={device_type}")
            
        except Exception as e:
            logger.error(f"发送消息到设备类型失败: {e}")
            raise
    
    async def broadcast_presence_change(self, user_id: str, event_type: str) -> None:
        """广播在线状态变化"""
        try:
            message = {
                "event_type": event_type,
                "user_id": user_id,
                "instance_id": self.instance_id,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis_client.publish(self.presence_channel, json.dumps(message))
            logger.debug(f"在线状态变化已广播: {user_id} -> {event_type}")
            
        except Exception as e:
            logger.error(f"广播在线状态变化失败: {e}")
            raise
    
    async def broadcast_device_change(self, user_id: str, connection_id: str, 
                                    event_type: str, device_metadata: Optional[Dict[str, Any]] = None) -> None:
        """广播设备连接状态变化"""
        try:
            message = {
                "event_type": event_type,
                "user_id": user_id,
                "connection_id": connection_id,
                "device_type": device_metadata.get("device_type", "unknown") if device_metadata else "unknown",
                "device_id": device_metadata.get("device_id") if device_metadata else None,
                "instance_id": self.instance_id,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis_client.publish(self.presence_channel, json.dumps(message))
            logger.debug(f"设备状态变化已广播: {event_type}, user_id={user_id}, connection_id={connection_id}")
            
        except Exception as e:
            logger.error(f"广播设备状态变化失败: {e}")
            raise
    
    async def send_to_local_connections(self, connections: Set[WebSocket], payload: Dict[str, Any]) -> tuple[int, list[WebSocket]]:
        """向本地连接发送消息"""
        success_count = 0
        disconnected_connections = []
        
        for websocket in connections:
            try:
                await websocket.send_json(payload)
                success_count += 1
            except Exception as e:
                logger.warning(f"向WebSocket发送消息失败: {e}")
                disconnected_connections.append(websocket)
        
        if success_count > 0:
            logger.debug(f"本地消息发送成功: count={success_count}")
        
        return success_count, disconnected_connections
    
    def parse_broadcast_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析广播消息"""
        try:
            payload = data.get("payload")
            if not payload:
                return {}
            
            return {
                "target_connection_id": data.get("target_connection_id"),
                "target_user_id": data.get("target_user_id"),
                "target_device_type": data.get("target_device_type"),
                "payload": payload
            }
        except Exception as e:
            logger.error(f"解析广播消息失败: {e}")
            return {}
    
    def parse_presence_message(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析在线状态消息"""
        try:
            return {
                "event_type": data.get("event_type"),
                "user_id": data.get("user_id"),
                "connection_id": data.get("connection_id"),
                "device_type": data.get("device_type"),
                "device_id": data.get("device_id")
            }
        except Exception as e:
            logger.error(f"解析在线状态消息失败: {e}")
            return {}
