"""
WebSocket领域Schema
包含WebSocket连接、消息传输等相关的数据模型
注意：当前项目主要使用前端WebSocket客户端，后端Schema暂时保留供将来扩展使用
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel


class WebSocketMessage(BaseModel):
    """WebSocket消息模型"""
    action: Literal[
        "connect", "disconnect", "message", "typing", 
        "read", "takeover", "switchtoai", "error"
    ]
    data: Optional[dict] = None
    conversation_id: Optional[str] = None
    sender_id: Optional[str] = None
    timestamp: Optional[datetime] = None


class WebSocketConnectionInfo(BaseModel):
    """WebSocket连接信息模型"""
    connection_id: str
    user_id: str
    conversation_id: Optional[str] = None
    connected_at: datetime
    last_activity: datetime
    status: Literal["connected", "disconnected", "reconnecting"]


class WebSocketError(BaseModel):
    """WebSocket错误模型"""
    error_code: str
    error_message: str
    timestamp: datetime
    connection_id: Optional[str] = None
    details: Optional[dict] = None


class WebSocketStats(BaseModel):
    """WebSocket统计信息模型"""
    total_connections: int
    active_connections: int
    messages_sent: int
    messages_received: int
    errors_count: int
    uptime_seconds: float 