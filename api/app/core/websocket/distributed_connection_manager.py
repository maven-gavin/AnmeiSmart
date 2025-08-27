"""
分布式WebSocket连接管理器 - 基于Redis Pub/Sub的可扩展架构
重构版本：使用组合模式，职责分离
"""
import asyncio
import json
import logging
from typing import Dict, Set, Optional, List, Any
from datetime import datetime
import uuid

import redis.asyncio as aioredis
from fastapi import WebSocket, WebSocketDisconnect

from app.core.redis_client import RedisClient
from .connection_manager import ConnectionManager, ConnectionLimitExceeded
from .message_router import MessageRouter, MessageTooLarge, MessageRateLimitExceeded
from .presence_manager import PresenceManager

logger = logging.getLogger(__name__)


class DistributedConnectionManager:
    """
    分布式WebSocket连接管理器
    使用组合模式，将职责分离到专门的管理器中
    """
    
    def __init__(self, redis_client: RedisClient,
                 max_connections_per_user: int = 5,
                 max_message_size: int = 1024 * 1024,  # 1MB
                 rate_limit_window: int = 60,  # 秒
                 rate_limit_max_messages: int = 100):
        
        # 初始化各个专门的管理器
        self.connection_manager = ConnectionManager(max_connections_per_user)
        self.message_router = MessageRouter(
            redis_client, 
            max_message_size, 
            rate_limit_window, 
            rate_limit_max_messages
        )
        self.presence_manager = PresenceManager(redis_client)
        
        # Redis客户端
        self.redis_client = redis_client
        
        # 实例标识
        self.instance_id = str(uuid.uuid4())[:8]
        
        # 监听任务
        self.pubsub_task: Optional[asyncio.Task] = None
        self.presence_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        
        # 锁，用于保护并发操作
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """初始化管理器，启动Redis监听器"""
        try:
            # 启动消息广播监听器
            self.pubsub_task = asyncio.create_task(self._broadcast_listener())
            
            # 启动在线状态监听器
            self.presence_task = asyncio.create_task(self._presence_listener())
            
            # 启动定期清理任务
            self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
            logger.info(f"分布式连接管理器已初始化 [实例ID: {self.instance_id}]")
        except Exception as e:
            logger.error(f"初始化分布式连接管理器失败: {e}")
            raise
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 取消所有任务
            tasks = [self.pubsub_task, self.presence_task, self.cleanup_task]
            for task in tasks:
                if task:
                    task.cancel()
            
            # 等待任务完成
            for task in tasks:
                if task:
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # 清理所有本地连接的在线状态
            for user_id in list(self.connection_manager.connections_by_user.keys()):
                await self.presence_manager.remove_user_from_online(user_id)
            
            logger.info(f"分布式连接管理器已清理 [实例ID: {self.instance_id}]")
        except Exception as e:
            logger.error(f"清理分布式连接管理器失败: {e}")
    
    async def _broadcast_listener(self):
        """监听广播频道的后台任务"""
        redis_client = await self.redis_client.get_client()
        async with redis_client.pubsub() as pubsub:
            await pubsub.subscribe(self.message_router.broadcast_channel)
            logger.info(f"开始监听广播频道: {self.message_router.broadcast_channel}")
            
            while True:
                try:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message and message.get("type") == "message":
                        await self._handle_broadcast_message(json.loads(message["data"]))
                except asyncio.CancelledError:
                    logger.info("广播监听器已取消")
                    break
                except Exception as e:
                    logger.error(f"处理广播消息失败: {e}")
                    await asyncio.sleep(1)
    
    async def _presence_listener(self):
        """监听在线状态变化的后台任务"""
        redis_client = await self.redis_client.get_client()
        async with redis_client.pubsub() as pubsub:
            await pubsub.subscribe(self.message_router.presence_channel)
            logger.info(f"开始监听在线状态频道: {self.message_router.presence_channel}")
            
            while True:
                try:
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                    if message and message.get("type") == "message":
                        await self._handle_presence_message(json.loads(message["data"]))
                except asyncio.CancelledError:
                    logger.info("在线状态监听器已取消")
                    break
                except Exception as e:
                    logger.error(f"处理在线状态消息失败: {e}")
                    await asyncio.sleep(1)
    
    async def _periodic_cleanup(self):
        """定期清理任务"""
        while True:
            try:
                await asyncio.sleep(300)  # 每5分钟清理一次
                await self._perform_cleanup()
            except asyncio.CancelledError:
                logger.info("定期清理任务已取消")
                break
            except Exception as e:
                logger.error(f"定期清理失败: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再试
    
    async def _perform_cleanup(self):
        """执行清理操作"""
        try:
            # 清理断开的连接
            disconnected_count = await self.connection_manager.cleanup_disconnected_connections()
            
            # 清理僵尸用户
            active_user_ids = set(self.connection_manager.connections_by_user.keys())
            stale_count = await self.presence_manager.cleanup_stale_users(active_user_ids)
            
            if disconnected_count > 0 or stale_count > 0:
                logger.info(f"清理完成: 断开连接 {disconnected_count}, 僵尸用户 {stale_count}")
                
        except Exception as e:
            logger.error(f"执行清理操作失败: {e}")
    
    async def _handle_broadcast_message(self, data: dict):
        """处理接收到的广播消息"""
        try:
            parsed_data = self.message_router.parse_broadcast_message(data)
            if not parsed_data:
                return
            
            payload = parsed_data.get("payload")
            if not payload:
                return
            
            # 按连接ID发送（精确设备）
            target_connection_id = parsed_data.get("target_connection_id")
            if target_connection_id:
                await self._send_to_local_connection(target_connection_id, payload)
                return
            
            # 按用户ID和设备类型发送
            target_user_id = parsed_data.get("target_user_id")
            target_device_type = parsed_data.get("target_device_type")
            if target_user_id and target_device_type:
                await self._send_to_local_user_device_type(target_user_id, target_device_type, payload)
                return
            
            # 按用户ID发送（所有设备）
            if target_user_id:
                await self._send_to_local_user(target_user_id, payload)
                
        except Exception as e:
            logger.error(f"处理广播消息失败: {e}")
    
    async def _handle_presence_message(self, data: dict):
        """处理在线状态变化消息"""
        try:
            parsed_data = self.message_router.parse_presence_message(data)
            if not parsed_data:
                return
            
            event_type = parsed_data.get("event_type")
            user_id = parsed_data.get("user_id")
            
            if event_type and user_id:
                # 广播在线状态变化给所有连接的用户
                presence_payload = {
                    "event": "presence_update",
                    "data": {
                        "user_id": user_id,
                        "status": "online" if event_type == "user_online" else "offline",
                        "timestamp": datetime.now().isoformat()
                    }
                }
                
                # 发送给所有本地连接的用户
                for local_user_id in self.connection_manager.connections_by_user:
                    await self._send_to_local_user(local_user_id, presence_payload)
                    
        except Exception as e:
            logger.error(f"处理在线状态消息失败: {e}")
    
    async def connect(self, user_id: str, websocket: WebSocket, 
                     metadata: Optional[Dict[str, Any]] = None, 
                     connection_id: Optional[str] = None) -> bool:
        """建立WebSocket连接"""
        async with self._lock:
            try:
                # 使用连接管理器建立连接
                connection_id = await self.connection_manager.connect(user_id, websocket, metadata, connection_id)
                
                # 更新在线状态
                was_online = await self.presence_manager.add_user_to_online(user_id)
                
                if not was_online:
                    # 用户首次上线，广播在线状态
                    await self.message_router.broadcast_presence_change(user_id, "user_online")
                else:
                    # 用户新设备上线，广播设备连接状态
                    await self.message_router.broadcast_device_change(
                        user_id, connection_id, "device_connected", metadata
                    )
                
                logger.info(f"用户连接成功: {user_id}, 连接ID: {connection_id} [实例: {self.instance_id}]")
                return True
                
            except ConnectionLimitExceeded as e:
                logger.warning(f"连接数量超限: {e}")
                return False
            except Exception as e:
                logger.error(f"建立WebSocket连接失败: {e}")
                return False
    
    async def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        try:
            # 获取连接信息
            metadata = self.connection_manager.get_connection_metadata(websocket)
            if not metadata:
                return
            
            user_id = metadata["user_id"]
            connection_id = metadata.get("connection_id")
            
            # 使用连接管理器断开连接
            await self.connection_manager.disconnect(websocket)
            
            # 检查用户是否完全离线
            if not self.connection_manager.is_user_connected(user_id):
                was_online = await self.presence_manager.remove_user_from_online(user_id)
                if was_online:
                    # 用户完全离线，广播离线状态
                    await self.message_router.broadcast_presence_change(user_id, "user_offline")
            else:
                # 用户还有其他设备在线，广播设备断开状态
                if connection_id:
                    await self.message_router.broadcast_device_change(
                        user_id, connection_id, "device_disconnected", metadata.get("metadata")
                    )
            
            logger.info(f"用户连接断开: {user_id}, 连接ID: {connection_id} [实例: {self.instance_id}]")
            
        except Exception as e:
            logger.error(f"断开WebSocket连接失败: {e}")
    
    async def send_to_user(self, user_id: str, payload: dict):
        """向指定用户发送消息"""
        try:
            await self.message_router.send_to_user(user_id, payload)
        except (MessageTooLarge, MessageRateLimitExceeded) as e:
            logger.warning(f"发送消息失败: {e}")
            raise
        except Exception as e:
            logger.error(f"发送消息到用户失败: {e}")
            raise
    
    async def send_to_device(self, connection_id: str, payload: dict):
        """向指定设备发送消息"""
        try:
            await self.message_router.send_to_device(connection_id, payload)
        except MessageTooLarge as e:
            logger.warning(f"发送消息失败: {e}")
            raise
        except Exception as e:
            logger.error(f"发送消息到设备失败: {e}")
            raise
    
    async def send_to_device_type(self, user_id: str, device_type: str, payload: dict):
        """向用户的特定类型设备发送消息"""
        try:
            await self.message_router.send_to_device_type(user_id, device_type, payload)
        except (MessageTooLarge, MessageRateLimitExceeded) as e:
            logger.warning(f"发送消息失败: {e}")
            raise
        except Exception as e:
            logger.error(f"发送消息到设备类型失败: {e}")
            raise
    
    async def _send_to_local_user(self, user_id: str, payload: dict):
        """向本地连接的用户发送消息"""
        connections = self.connection_manager.get_user_connections(user_id)
        if not connections:
            return
        
        success_count, disconnected_connections = await self.message_router.send_to_local_connections(connections, payload)
        
        # 清理断开的连接
        for websocket in disconnected_connections:
            await self.disconnect(websocket)
        
        if success_count > 0:
            logger.debug(f"本地消息发送成功: user_id={user_id}, count={success_count}")
    
    async def _send_to_local_connection(self, connection_id: str, payload: dict):
        """向本地特定连接发送消息"""
        websocket = self.connection_manager.get_connection_by_id(connection_id)
        if not websocket:
            return
        
        try:
            await websocket.send_json(payload)
            logger.debug(f"本地连接消息发送成功: connection_id={connection_id}")
        except Exception as e:
            logger.warning(f"向连接 {connection_id} 发送消息失败: {e}")
            await self.disconnect(websocket)
    
    async def _send_to_local_user_device_type(self, user_id: str, device_type: str, payload: dict):
        """向本地用户的特定设备类型发送消息"""
        connections = self.connection_manager.get_connections_by_device_type(user_id, device_type)
        if not connections:
            return
        
        success_count, disconnected_connections = await self.message_router.send_to_local_connections(connections, payload)
        
        # 清理断开的连接
        for websocket in disconnected_connections:
            await self.disconnect(websocket)
        
        if success_count > 0:
            logger.debug(f"本地设备类型消息发送成功: user_id={user_id}, device_type={device_type}, count={success_count}")
    
    # 代理方法 - 提供统一的接口
    async def is_user_online(self, user_id: str) -> bool:
        """检查用户是否在线"""
        return await self.presence_manager.is_user_online(user_id)
    
    async def get_online_users(self) -> Set[str]:
        """获取所有在线用户列表"""
        return await self.presence_manager.get_online_users()
    
    def get_local_connection_count(self) -> int:
        """获取本地连接数量"""
        return self.connection_manager.get_total_connection_count()
    
    def get_local_user_count(self) -> int:
        """获取本地用户数量"""
        return self.connection_manager.get_total_user_count()
    
    def get_user_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有设备的连接信息"""
        return self.connection_manager.get_user_devices(user_id)
    
    async def get_statistics(self) -> dict:
        """获取系统统计信息"""
        try:
            presence_stats = await self.presence_manager.get_online_statistics()
            
            return {
                "instance_id": self.instance_id,
                "local_connections": self.connection_manager.get_total_connection_count(),
                "local_users": self.connection_manager.get_total_user_count(),
                "presence": presence_stats,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                "instance_id": self.instance_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            } 