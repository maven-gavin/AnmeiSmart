"""
WebSocket领域Schema
包含WebSocket连接、消息传输、广播和通知相关的数据模型
"""
from datetime import datetime
from typing import Optional, Literal, Dict, Any, List, Union
from pydantic import BaseModel, Field


class WebSocketMessage(BaseModel):
    """WebSocket消息模型 (通用)"""
    action: str
    data: Optional[Dict[str, Any]] = None
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
    details: Optional[Dict[str, Any]] = None


class WebSocketStats(BaseModel):
    """WebSocket统计信息模型"""
    total_connections: int
    active_connections: int
    messages_sent: int
    messages_received: int
    errors_count: int
    uptime_seconds: float


# ==========================================
# 广播和通知相关 Schema (新增优化)
# ==========================================

class NotificationData(BaseModel):
    """推送通知数据模型"""
    title: str
    body: str
    conversation_id: Optional[str] = None
    action: Optional[str] = None
    priority: Literal["high", "normal", "low"] = "normal"
    extra_data: Optional[Dict[str, Any]] = None


class BroadcastPayload(BaseModel):
    """广播消息负载基础模型"""
    action: str
    data: Dict[str, Any]
    conversation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class TypingStatusData(BaseModel):
    """输入状态数据"""
    user_id: str
    is_typing: bool


class ReadStatusData(BaseModel):
    """已读状态数据"""
    user_id: str
    message_ids: List[str]


class SystemNotificationData(BaseModel):
    """系统通知数据"""
    title: str
    message: str
    type: str = "info"
    extra: Optional[Dict[str, Any]] = None
