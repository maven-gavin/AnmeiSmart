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

    @staticmethod
    def from_model(message) -> "MessageInfo":
        if not message:
            return None
        sender = MessageSender(
            id=message.sender_id or "system",
            name=(
                "系统" if message.sender_type == "system"
                else "AI助手" if message.sender_type == "ai"
                else getattr(message.sender, "username", "未知用户")
            ),
            avatar=getattr(message.sender, "avatar", None),
            type=message.sender_type
        )
        return MessageInfo(
            id=message.id,
            conversation_id=message.conversation_id,
            content=message.content,
            type=message.type,
            sender=sender,
            timestamp=message.timestamp,
            is_read=message.is_read,
            is_important=message.is_important
        )


class ConversationBase(BaseModel):
    """会话基础模型"""
    title: str
    customer_id: str
    is_ai_controlled: bool = True


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
    is_ai_controlled: bool = True

    @staticmethod
    def from_model(conversation, last_message=None, unread_count=0):
        """从 ORM Conversation 实例和 last_message 构建 ConversationInfo"""
        customer = None
        if getattr(conversation, 'customer', None):
            customer = {
                "id": conversation.customer.id,
                "username": conversation.customer.username,
                "avatar": conversation.customer.avatar or '/avatars/user.png'
            }
        last_msg_schema = None
        if last_message:
            last_msg_schema = MessageInfo.from_model(last_message)
        return ConversationInfo(
            id=conversation.id,
            title=conversation.title,
            customer_id=conversation.customer_id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            is_active=conversation.is_active,
            customer=customer,
            last_message=last_msg_schema,
            is_ai_controlled=conversation.is_ai_controlled
        )


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