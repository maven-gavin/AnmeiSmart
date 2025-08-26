"""
分布式WebSocket连接管理器 - 基于Redis Pub/Sub的可扩展架构
"""
import asyncio
import json
import logging
from typing import Dict, Set, Optional, List, Any
from datetime import datetime
import uuid

import redis.asyncio as aioredis
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class DistributedConnectionManager:
    """
    分布式WebSocket连接管理器
    - 使用Redis管理在线用户状态
    - 使用Redis Pub/Sub实现跨实例消息广播
    - 每个实例只管理本地WebSocket连接
    """
    
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        # 按用户ID组织的连接（兼容现有逻辑）
        self.local_connections: Dict[str, Set[WebSocket]] = {}  # user_id -> WebSocket集合
        # 按连接ID组织的连接（支持多设备区分）
        self.connections_by_id: Dict[str, WebSocket] = {}       # connection_id -> WebSocket
        # 连接元数据
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}     # WebSocket -> 元数据
        # 反向映射：WebSocket -> connection_id
        self.websocket_to_connection_id: Dict[WebSocket, str] = {}
        
        # Redis键名配置
        self.online_users_key = "ws:online_users"
        self.broadcast_channel = "ws:broadcast"
        self.presence_channel = "ws:presence"
        
        # 实例标识
        self.instance_id = str(uuid.uuid4())[:8]
        
        # 监听任务
        self.pubsub_task: Optional[asyncio.Task] = None
        self.presence_task: Optional[asyncio.Task] = None
    
    async def initialize(self):
        """初始化管理器，启动Redis监听器"""
        try:
            # 启动消息广播监听器
            self.pubsub_task = asyncio.create_task(self._broadcast_listener())
            
            # 启动在线状态监听器
            self.presence_task = asyncio.create_task(self._presence_listener())
            
            logger.info(f"分布式连接管理器已初始化 [实例ID: {self.instance_id}]")
        except Exception as e:
            logger.error(f"初始化分布式连接管理器失败: {e}")
            raise
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 取消监听任务
            if self.pubsub_task:
                self.pubsub_task.cancel()
            if self.presence_task:
                self.presence_task.cancel()
            
            # 清理所有本地连接的在线状态
            for user_id in list(self.local_connections.keys()):
                await self._remove_user_from_online(user_id)
            
            logger.info(f"分布式连接管理器已清理 [实例ID: {self.instance_id}]")
        except Exception as e:
            logger.error(f"清理分布式连接管理器失败: {e}")
    
    async def _broadcast_listener(self):
        """监听广播频道的后台任务"""
        async with self.redis.pubsub() as pubsub:
            await pubsub.subscribe(self.broadcast_channel)
            logger.info(f"开始监听广播频道: {self.broadcast_channel}")
            
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
        async with self.redis.pubsub() as pubsub:
            await pubsub.subscribe(self.presence_channel)
            logger.info(f"开始监听在线状态频道: {self.presence_channel}")
            
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
    
    async def _handle_broadcast_message(self, data: dict):
        """处理接收到的广播消息（支持多设备路由）"""
        try:
            payload = data.get("payload")
            if not payload:
                return
            
            # 按连接ID发送（精确设备）
            target_connection_id = data.get("target_connection_id")
            if target_connection_id:
                await self._send_to_local_connection(target_connection_id, payload)
                return
            
            # 按用户ID和设备类型发送
            target_user_id = data.get("target_user_id")
            target_device_type = data.get("target_device_type")
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
            event_type = data.get("event_type")  # "user_online" | "user_offline"
            user_id = data.get("user_id")
            
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
                for local_user_id in self.local_connections:
                    await self._send_to_local_user(local_user_id, presence_payload)
                    
        except Exception as e:
            logger.error(f"处理在线状态消息失败: {e}")
    
    async def connect(self, user_id: str, websocket: WebSocket, metadata: Optional[Dict[str, Any]] = None, connection_id: Optional[str] = None) -> bool:
        """建立WebSocket连接（支持多设备）"""
        try:
            await websocket.accept()
            
            # 生成连接ID（如果没有提供）
            if not connection_id:
                connection_id = f"{user_id}_{self.instance_id}_{int(datetime.now().timestamp() * 1000)}"
            
            # 添加到本地连接管理（按用户ID）
            if user_id not in self.local_connections:
                self.local_connections[user_id] = set()
            self.local_connections[user_id].add(websocket)
            
            # 添加到连接ID映射（支持多设备区分）
            self.connections_by_id[connection_id] = websocket
            self.websocket_to_connection_id[websocket] = connection_id
            
            # 保存连接元数据
            self.connection_metadata[websocket] = {
                "user_id": user_id,
                "connection_id": connection_id,
                "connected_at": datetime.now(),
                "instance_id": self.instance_id,
                "device_type": metadata.get("device_type", "unknown") if metadata else "unknown",
                "device_id": metadata.get("device_id") if metadata else None,
                "metadata": metadata or {}
            }
            
            # 将用户标记为在线
            was_online = await self._add_user_to_online(user_id)
            
            if not was_online:
                # 用户首次上线，广播在线状态
                await self._broadcast_presence_change(user_id, "user_online")
            else:
                # 用户新设备上线，广播设备连接状态
                await self._broadcast_device_change(user_id, connection_id, "device_connected", metadata)
            
            logger.info(f"用户连接成功: {user_id}, 设备: {metadata.get('device_type', 'unknown') if metadata else 'unknown'}, 连接ID: {connection_id} [实例: {self.instance_id}]")
            return True
            
        except Exception as e:
            logger.error(f"建立WebSocket连接失败: {e}")
            return False
    
    async def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接（支持多设备）"""
        try:
            if websocket not in self.connection_metadata:
                return
            
            metadata = self.connection_metadata[websocket]
            user_id = metadata["user_id"]
            connection_id = metadata.get("connection_id")
            device_type = metadata.get("device_type", "unknown")
            
            # 从连接ID映射中移除
            if connection_id and connection_id in self.connections_by_id:
                del self.connections_by_id[connection_id]
            if websocket in self.websocket_to_connection_id:
                del self.websocket_to_connection_id[websocket]
            
            # 从本地连接中移除
            if user_id in self.local_connections:
                self.local_connections[user_id].discard(websocket)
                if not self.local_connections[user_id]:
                    del self.local_connections[user_id]
            
            # 广播设备断开状态（如果用户还有其他设备在线）
            if user_id in self.local_connections and connection_id:
                await self._broadcast_device_change(user_id, connection_id, "device_disconnected", metadata.get("metadata"))
            
            # 清理元数据
            del self.connection_metadata[websocket]
            
            # 检查用户是否完全离线
            if user_id not in self.local_connections:
                was_online = await self._remove_user_from_online(user_id)
                if was_online:
                    # 用户完全离线，广播离线状态
                    await self._broadcast_presence_change(user_id, "user_offline")
            
            logger.info(f"用户连接断开: {user_id}, 设备: {device_type}, 连接ID: {connection_id} [实例: {self.instance_id}]")
            
        except Exception as e:
            logger.error(f"断开WebSocket连接失败: {e}")
    
    async def send_to_user(self, user_id: str, payload: dict):
        """向指定用户发送消息（通过Redis广播）"""
        try:
            # 确保payload中的所有数据都是可序列化的
            serializable_payload = self._make_serializable(payload)
            
            message = {
                "target_user_id": user_id,
                "payload": serializable_payload,
                "instance_id": self.instance_id,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis.publish(self.broadcast_channel, json.dumps(message))
            logger.debug(f"消息已发布到Redis: user_id={user_id}")
            
        except Exception as e:
            logger.error(f"发送消息到Redis失败: {e}")
    
    def _make_serializable(self, obj):
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
    
    async def _send_to_local_user(self, user_id: str, payload: dict):
        """向本地连接的用户发送消息"""
        if user_id not in self.local_connections:
            return
        
        disconnected_connections = []
        success_count = 0
        
        for websocket in self.local_connections[user_id].copy():
            try:
                await websocket.send_json(payload)
                success_count += 1
            except Exception as e:
                logger.warning(f"向用户 {user_id} 发送消息失败: {e}")
                disconnected_connections.append(websocket)
        
        # 清理断开的连接
        for websocket in disconnected_connections:
            await self.disconnect(websocket)
        
        if success_count > 0:
            logger.debug(f"本地消息发送成功: user_id={user_id}, count={success_count}")
    
    async def _send_to_local_connection(self, connection_id: str, payload: dict):
        """向本地特定连接发送消息"""
        if connection_id not in self.connections_by_id:
            return
        
        websocket = self.connections_by_id[connection_id]
        try:
            await websocket.send_json(payload)
            logger.debug(f"本地连接消息发送成功: connection_id={connection_id}")
        except Exception as e:
            logger.warning(f"向连接 {connection_id} 发送消息失败: {e}")
            await self.disconnect(websocket)
    
    async def _send_to_local_user_device_type(self, user_id: str, device_type: str, payload: dict):
        """向本地用户的特定设备类型发送消息"""
        if user_id not in self.local_connections:
            return
        
        disconnected_connections = []
        success_count = 0
        
        for websocket in self.local_connections[user_id].copy():
            if websocket in self.connection_metadata:
                metadata = self.connection_metadata[websocket]
                if metadata.get("device_type") == device_type:
                    try:
                        await websocket.send_json(payload)
                        success_count += 1
                    except Exception as e:
                        logger.warning(f"向用户 {user_id} 的设备类型 {device_type} 发送消息失败: {e}")
                        disconnected_connections.append(websocket)
        
        # 清理断开的连接
        for websocket in disconnected_connections:
            await self.disconnect(websocket)
        
        if success_count > 0:
            logger.debug(f"本地设备类型消息发送成功: user_id={user_id}, device_type={device_type}, count={success_count}")
    
    async def _add_user_to_online(self, user_id: str) -> bool:
        """将用户添加到在线列表，返回用户之前是否在线"""
        try:
            # 使用Redis SADD，返回1表示新添加，0表示已存在
            result = await self.redis.sadd(self.online_users_key, user_id)
            return result == 0  # 返回之前是否在线
        except Exception as e:
            logger.error(f"添加用户到在线列表失败: {e}")
            return False
    
    async def _remove_user_from_online(self, user_id: str) -> bool:
        """从在线列表移除用户，返回用户之前是否在线"""
        try:
            # 使用Redis SREM，返回1表示成功移除，0表示不存在
            result = await self.redis.srem(self.online_users_key, user_id)
            return result == 1  # 返回之前是否在线
        except Exception as e:
            logger.error(f"从在线列表移除用户失败: {e}")
            return False
    
    async def _broadcast_presence_change(self, user_id: str, event_type: str):
        """广播在线状态变化"""
        try:
            message = {
                "event_type": event_type,
                "user_id": user_id,
                "instance_id": self.instance_id,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis.publish(self.presence_channel, json.dumps(message))
            logger.debug(f"在线状态变化已广播: {user_id} -> {event_type}")
            
        except Exception as e:
            logger.error(f"广播在线状态变化失败: {e}")
    
    async def is_user_online(self, user_id: str) -> bool:
        """检查用户是否在线"""
        try:
            result = await self.redis.sismember(self.online_users_key, user_id)
            return bool(result)
        except Exception as e:
            logger.error(f"检查用户在线状态失败: {e}")
            return False
    
    async def get_online_users(self) -> Set[str]:
        """获取所有在线用户列表"""
        try:
            result = await self.redis.smembers(self.online_users_key)
            return set(result) if result else set()
        except Exception as e:
            logger.error(f"获取在线用户列表失败: {e}")
            return set()
    
    def get_local_connection_count(self) -> int:
        """获取本地连接数量"""
        return sum(len(connections) for connections in self.local_connections.values())
    
    def get_local_user_count(self) -> int:
        """获取本地用户数量"""
        return len(self.local_connections)
    
    async def _broadcast_device_change(self, user_id: str, connection_id: str, event_type: str, device_metadata: Optional[Dict[str, Any]] = None):
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
            
            await self.redis.publish(self.presence_channel, json.dumps(message))
            logger.debug(f"设备状态变化已广播: {event_type}, user_id={user_id}, connection_id={connection_id}")
            
        except Exception as e:
            logger.error(f"广播设备状态变化失败: {e}")
    
    async def send_to_device(self, connection_id: str, payload: dict):
        """向指定设备连接发送消息"""
        try:
            message = {
                "target_connection_id": connection_id,
                "payload": payload,
                "instance_id": self.instance_id,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis.publish(self.broadcast_channel, json.dumps(message))
            logger.debug(f"消息已发布到Redis（按设备）: connection_id={connection_id}")
            
        except Exception as e:
            logger.error(f"发送消息到特定设备失败: {e}")
    
    async def send_to_device_type(self, user_id: str, device_type: str, payload: dict):
        """向用户的特定类型设备发送消息"""
        try:
            message = {
                "target_user_id": user_id,
                "target_device_type": device_type,
                "payload": payload,
                "instance_id": self.instance_id,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis.publish(self.broadcast_channel, json.dumps(message))
            logger.debug(f"消息已发布到Redis（按设备类型）: user_id={user_id}, device_type={device_type}")
            
        except Exception as e:
            logger.error(f"发送消息到特定设备类型失败: {e}")
    
    def get_user_devices(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有设备的连接信息"""
        devices = []
        if user_id in self.local_connections:
            for websocket in self.local_connections[user_id]:
                if websocket in self.connection_metadata:
                    metadata = self.connection_metadata[websocket]
                    devices.append({
                        "connection_id": metadata.get("connection_id"),
                        "device_type": metadata.get("device_type", "unknown"),
                        "device_id": metadata.get("device_id"),
                        "connected_at": metadata.get("connected_at"),
                        "instance_id": metadata.get("instance_id")
                    })
        return devices 