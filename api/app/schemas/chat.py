from datetime import datetime
from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class MessageSender(BaseModel):
    """消息发送者信息"""
    id: str
    name: str
    avatar: Optional[str] = None
    type: Literal["customer", "consultant", "doctor", "ai", "system"]


class MessageBase(BaseModel):
    """消息基础模型"""
    content: str
    type: Literal["text", "image", "voice", "file", "system"]


class MessageCreate(MessageBase):
    """创建消息的请求模型"""
    conversation_id: str
    sender_id: str
    sender_type: Literal["customer", "consultant", "doctor", "ai", "system"]


class MessageInfo(MessageBase):
    """消息完整模型"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    sender: MessageSender
    timestamp: datetime
    is_read: bool = False
    is_important: bool = False


class ConversationBase(BaseModel):
    """会话基础模型"""
    title: str
    customer_id: str


class ConversationCreate(ConversationBase):
    """创建会话的请求模型"""
    pass


class ConversationInfo(ConversationBase):
    """会话完整模型"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,  # 允许使用别名
        json_schema_extra={
            "example": {
                "id": "conv_123456",
                "title": "咨询会话",
                "customer_id": "usr_123456",
                "created_at": "2025-05-21T14:37:57.708339",
                "updated_at": "2025-05-21T14:37:57.708339",
                "is_active": True,
                "customer": {
                    "id": "usr_123456",
                    "username": "王先生",
                    "email": "example@example.com",
                    "avatar": "/avatars/user.png"
                }
            }
        }
    )

    id: str
    last_message: Optional["MessageInfo"] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True
    customer: Optional[dict] = Field(None, description="客户信息")


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