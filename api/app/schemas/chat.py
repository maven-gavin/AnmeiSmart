"""
聊天领域Schema
包含消息、会话等聊天相关的数据模型
"""
from datetime import datetime
from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
import json

# 从文件领域导入FileInfo，用于文件消息的处理
from .file import FileInfo


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


class MessageCreateRequest(MessageBase):
    """HTTP API创建消息的请求模型 - 不包含会自动推导的字段"""
    pass


class AIChatRequest(MessageBase):
    """AI聊天请求模型 - 用于AI端点，不包含发送者信息（从当前用户推导）"""
    conversation_id: str


class MessageInfo(MessageBase):
    """消息完整模型"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    sender: MessageSender
    timestamp: datetime
    is_read: bool = False
    is_important: bool = False
    file_info: Optional[FileInfo] = None  # 文件消息的文件信息

    @staticmethod
    def from_model(message) -> "MessageInfo":
        if not message:
            return None
        
        # 安全地获取sender_id，处理可能缺少的属性
        sender_id = getattr(message, 'sender_id', None) or "system"
        sender_type = getattr(message, 'sender_type', 'system')
        
        # 安全地获取sender对象
        sender_obj = getattr(message, 'sender', None)
        sender_name = "系统"
        sender_avatar = None
        
        if sender_type == "system":
            sender_name = "系统"
            sender_avatar = "/avatars/system.png"
        elif sender_type == "ai":
            sender_name = "AI助手"
            sender_avatar = "/avatars/ai.png"
        elif sender_obj:
            sender_name = getattr(sender_obj, "username", "未知用户")
            sender_avatar = getattr(sender_obj, "avatar", None)
        else:
            sender_name = "未知用户"
        
        sender = MessageSender(
            id=sender_id,
            name=sender_name,
            avatar=sender_avatar,
            type=sender_type
        )
        
        # 处理文件消息的内容
        content = getattr(message, 'content', '')
        message_type = getattr(message, 'type', 'text')
        file_info = None
        
        # 如果是文件消息，解析文件信息
        if message_type == 'file' and content:
            try:
                file_data = json.loads(content) if isinstance(content, str) else content
                if isinstance(file_data, dict) and 'file_url' in file_data:
                    file_info = FileInfo(**file_data)
                    # 对于文件消息，content显示文件名
                    content = file_data.get('file_name', '文件')
            except (json.JSONDecodeError, TypeError, ValueError):
                # 如果解析失败，保持原始内容
                pass
        
        return MessageInfo(
            id=getattr(message, 'id', ''),
            conversation_id=getattr(message, 'conversation_id', ''),
            content=content,
            type=message_type,
            sender=sender,
            timestamp=getattr(message, 'timestamp', datetime.now()),
            is_read=getattr(message, 'is_read', False),
            is_important=getattr(message, 'is_important', False),
            file_info=file_info
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
        
        # 安全地处理is_ai_controlled可能为None的情况
        is_ai_controlled = getattr(conversation, 'is_ai_controlled', True)
        if is_ai_controlled is None:
            is_ai_controlled = True
            
        return ConversationInfo(
            id=conversation.id,
            title=conversation.title,
            customer_id=conversation.customer_id,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            is_active=getattr(conversation, 'is_active', True),
            customer=customer,
            last_message=last_msg_schema,
            is_ai_controlled=is_ai_controlled
        )