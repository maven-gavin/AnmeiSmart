"""
WebSocket连接管理器 - 负责连接生命周期管理
"""
import asyncio
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime
import uuid
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionLimitExceeded(Exception):
    """连接数量超限异常"""
    pass


class ConnectionManager:
    """WebSocket连接管理器 - 专注于连接生命周期管理"""
    
    def __init__(self, max_connections_per_user: int = 5):
        self.max_connections_per_user = max_connections_per_user
        
        # 连接存储
        self.connections_by_user: Dict[str, Set[WebSocket]] = {}  # user_id -> WebSocket集合
        self.connections_by_id: Dict[str, WebSocket] = {}         # connection_id -> WebSocket
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}  # WebSocket -> 元数据
        self.websocket_to_connection_id: Dict[WebSocket, str] = {}      # WebSocket -> connection_id
        
        # 并发控制
        self._lock = asyncio.Lock()
        
        # 实例标识
        self.instance_id = str(uuid.uuid4())[:8]
    
    async def connect(self, user_id: str, websocket: WebSocket, 
                     metadata: Optional[Dict[str, Any]] = None, 
                     connection_id: Optional[str] = None) -> str:
        """建立WebSocket连接"""
        async with self._lock:
            try:
                # 检查连接数量限制
                if user_id in self.connections_by_user:
                    if len(self.connections_by_user[user_id]) >= self.max_connections_per_user:
                        raise ConnectionLimitExceeded(
                            f"用户 {user_id} 连接数已达上限 {self.max_connections_per_user}"
                        )
                
                # 接受WebSocket连接
                await websocket.accept()
                
                # 生成连接ID
                if not connection_id:
                    connection_id = f"{user_id}_{self.instance_id}_{int(datetime.now().timestamp() * 1000)}"
                
                # 添加到连接管理
                if user_id not in self.connections_by_user:
                    self.connections_by_user[user_id] = set()
                self.connections_by_user[user_id].add(websocket)
                
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
                
                logger.info(f"连接建立成功: user_id={user_id}, connection_id={connection_id}")
                return connection_id
                
            except Exception as e:
                logger.error(f"建立连接失败: {e}")
                raise
    
    async def disconnect(self, websocket: WebSocket) -> Optional[str]:
        """断开WebSocket连接"""
        try:
            if websocket not in self.connection_metadata:
                return None
            
            metadata = self.connection_metadata[websocket]
            user_id = metadata["user_id"]
            connection_id = metadata.get("connection_id")
            
            # 从连接管理中移除
            if connection_id and connection_id in self.connections_by_id:
                del self.connections_by_id[connection_id]
            if websocket in self.websocket_to_connection_id:
                del self.websocket_to_connection_id[websocket]
            
            if user_id in self.connections_by_user:
                self.connections_by_user[user_id].discard(websocket)
                if not self.connections_by_user[user_id]:
                    del self.connections_by_user[user_id]
            
            # 清理元数据
            del self.connection_metadata[websocket]
            
            logger.info(f"连接断开: user_id={user_id}, connection_id={connection_id}")
            return connection_id
            
        except Exception as e:
            logger.error(f"断开连接失败: {e}")
            return None
    
    def get_user_connections(self, user_id: str) -> Set[WebSocket]:
        """获取用户的所有连接"""
        return self.connections_by_user.get(user_id, set()).copy()
    
    def get_connection_by_id(self, connection_id: str) -> Optional[WebSocket]:
        """根据连接ID获取WebSocket"""
        return self.connections_by_id.get(connection_id)
    
    def get_connection_metadata(self, websocket: WebSocket) -> Optional[Dict[str, Any]]:
        """获取连接元数据"""
        return self.connection_metadata.get(websocket)
    
    def get_user_connection_count(self, user_id: str) -> int:
        """获取用户的连接数量"""
        return len(self.connections_by_user.get(user_id, set()))
    
    def get_total_connection_count(self) -> int:
        """获取总连接数量"""
        return len(self.connections_by_id)
    
    def get_total_user_count(self) -> int:
        """获取总用户数量"""
        return len(self.connections_by_user)
    
    def is_user_connected(self, user_id: str) -> bool:
        """检查用户是否已连接"""
        return user_id in self.connections_by_user and len(self.connections_by_user[user_id]) > 0
    
    def get_user_devices(self, user_id: str) -> list[Dict[str, Any]]:
        """获取用户所有设备的连接信息"""
        devices = []
        if user_id in self.connections_by_user:
            for websocket in self.connections_by_user[user_id]:
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
    
    def get_connections_by_device_type(self, user_id: str, device_type: str) -> Set[WebSocket]:
        """获取用户特定设备类型的连接"""
        connections = set()
        if user_id in self.connections_by_user:
            for websocket in self.connections_by_user[user_id]:
                if websocket in self.connection_metadata:
                    metadata = self.connection_metadata[websocket]
                    if metadata.get("device_type") == device_type:
                        connections.add(websocket)
        return connections
    
    async def cleanup_disconnected_connections(self) -> int:
        """清理断开的连接"""
        disconnected_count = 0
        disconnected_websockets = []
        
        for websocket in list(self.connection_metadata.keys()):
            try:
                # 尝试发送ping来检查连接状态
                await websocket.ping()
            except Exception:
                # 连接已断开
                disconnected_websockets.append(websocket)
                disconnected_count += 1
        
        # 批量清理断开的连接
        for websocket in disconnected_websockets:
            await self.disconnect(websocket)
        
        if disconnected_count > 0:
            logger.info(f"清理了 {disconnected_count} 个断开的连接")
        
        return disconnected_count
