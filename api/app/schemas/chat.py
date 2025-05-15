from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, ConfigDict


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


class Message(MessageBase):
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


class Conversation(ConversationBase):
    """会话完整模型"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    last_message: Optional[Message] = None
    created_at: datetime
    updated_at: datetime
    is_active: bool = True


class CustomerProfileBase(BaseModel):
    """客户档案基础模型"""
    name: str
    gender: Optional[str] = None
    age: Optional[int] = None
    contact: Optional[str] = None


class CustomerProfile(CustomerProfileBase):
    """客户档案完整模型"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    avatar: Optional[str] = None
    medical_history: Optional[str] = None
    allergies: Optional[List[str]] = None
    preferences: Optional[str] = None
    tags: Optional[List[str]] = None
    created_at: datetime
    updated_at: datetime


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