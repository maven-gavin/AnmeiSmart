"""
聊天领域Schema
包含消息、会话等聊天相关的数据模型

支持统一消息模型的四种类型：
- text: 纯文本消息
- media: 媒体文件消息（图片、语音、视频、文档等）
- system: 系统事件消息（如用户加入、接管状态等）
- structured: 结构化卡片消息（服务推荐等）
"""
from datetime import datetime
from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator
from enum import Enum

import logging
logger = logging.getLogger(__name__)
class MessageSender(BaseModel):
    """消息发送者信息"""
    id: str
    name: str
    avatar: Optional[str] = None
    type: Literal["chat", "system"]


# ===== 消息内容结构定义 =====

class TextMessageContent(BaseModel):
    """文本消息内容结构"""
    text: str


class MediaInfo(BaseModel):
    """媒体信息结构"""
    url: str
    name: str
    mime_type: str
    size_bytes: int
    metadata: Optional[Dict[str, Any]] = None  # 如：{"width": 800, "height": 600, "duration_seconds": 35.2}


class MediaMessageContent(BaseModel):
    """媒体消息内容结构"""
    text: Optional[str] = None  # 附带的文字消息（可选）
    media_info: MediaInfo


class SystemEventContent(BaseModel):
    """系统事件内容结构"""
    system_event_type: str  # 如："user_joined", "user_left", "takeover", "release"
    status: Optional[str] = None  # 事件状态
    participants: Optional[List[str]] = None  # 参与者
    duration_seconds: Optional[int] = None  # 持续时间（如通话）
    call_id: Optional[str] = None  # 通话ID
    details: Optional[Dict[str, Any]] = None  # 其他详细信息


class CardComponent(BaseModel):
    """通用卡片组件数据"""
    type: Literal["button", "text", "image", "divider"]
    content: Optional[Any] = None
    action: Optional[Dict[str, Any]] = None


class CardAction(BaseModel):
    """卡片操作"""
    text: str
    action: str
    data: Optional[Dict[str, Any]] = None


class StructuredMessageContent(BaseModel):
    """结构化消息内容（卡片式消息）"""
    card_type: Literal["service_recommendation", "custom"]
    title: str
    subtitle: Optional[str] = None
    data: Dict[str, Any]  # 根据card_type确定具体数据结构
    components: Optional[List[CardComponent]] = None  # 可选的交互组件
    actions: Optional[Dict[str, CardAction]] = None  # primary、secondary等操作


# ===== 消息模型定义 =====

class MessageBase(BaseModel):
    """消息基础模型"""
    content: Dict[str, Any]  # 结构化内容
    type: Literal["text", "media", "system", "structured"]


class MessageCreate(MessageBase):
    """创建消息的请求模型"""
    conversation_id: str
    sender_id: str
    sender_type: Literal["customer", "consultant", "doctor", "ai", "system", "digital_human"]
    reply_to_message_id: Optional[str] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class MessageCreateRequest(MessageBase):
    """HTTP API创建消息的请求模型 - 不包含会自动推导的字段"""
    is_important: Optional[bool] = False
    reply_to_message_id: Optional[str] = None
    extra_metadata: Optional[Dict[str, Any]] = None


class AIChatRequest(BaseModel):
    """AI聊天请求模型 - 用于AI端点，不包含发送者信息（从当前用户推导）"""
    conversation_id: str
    content: str  # 简化的文本内容
    type: Literal["text"] = "text"  # AI聊天目前只支持文本


# ===== 便利的创建请求模型 =====

class CreateTextMessageRequest(BaseModel):
    """创建文本消息请求"""
    text: str
    is_important: Optional[bool] = False
    reply_to_message_id: Optional[str] = None


class CreateMediaMessageRequest(BaseModel):
    """创建媒体消息请求"""
    media_url: str
    media_name: str
    mime_type: str
    size_bytes: int
    text: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_important: Optional[bool] = False
    reply_to_message_id: Optional[str] = None
    upload_method: Optional[str] = None


class CreateSystemEventRequest(BaseModel):
    """创建系统事件请求"""
    event_type: str
    status: Optional[str] = None
    event_data: Optional[Dict[str, Any]] = None


class CreateStructuredMessageRequest(BaseModel):
    """创建结构化消息请求"""
    card_type: str
    title: str
    subtitle: Optional[str] = None
    data: Dict[str, Any]
    components: Optional[List[Dict[str, Any]]] = None
    actions: Optional[Dict[str, Dict[str, Any]]] = None


class MessageInfo(MessageBase):
    """消息完整模型"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    sender: MessageSender
    timestamp: datetime
    is_read: bool = False
    is_important: bool = False
    reply_to_message_id: Optional[str] = None
    reactions: Optional[Dict[str, List[str]]] = None  # {"👍": ["user_id1", "user_id2"]}
    extra_metadata: Optional[Dict[str, Any]] = None

    # 便利属性
    @property
    def text_content(self) -> Optional[str]:
        """获取文本内容"""
        if self.type == "text":
            return self.content.get("text")
        elif self.type == "media":
            return self.content.get("text")  # 媒体消息的附带文字
        elif self.type == "structured":
            return self.content.get("title")  # 结构化消息的标题
        return None

    @property
    def media_info(self) -> Optional[MediaInfo]:
        """获取媒体信息（如果是媒体消息）"""
        if self.type == "media" and "media_info" in self.content:
            return MediaInfo(**self.content["media_info"])
        return None

    @property
    def structured_data(self) -> Optional[Dict[str, Any]]:
        """获取结构化消息数据"""
        if self.type == "structured":
            return self.content.get("data")
        return None

    @staticmethod
    def from_model(message) -> "MessageInfo":
        """从数据库模型转换为Schema模型"""
        if not message:
            return None
        
        # 获取sender信息
        sender_id = getattr(message, 'sender_id', None)
        sender_digital_human_id = getattr(message, 'sender_digital_human_id', None)
        sender_type = getattr(message, 'sender_type', 'chat')  # 默认为chat
        
        # 构建sender对象
        sender_name = "未知用户"
        sender_avatar = None
        actual_sender_id = "unknown"
        
        if sender_type == "system":
            # 系统消息
            sender_name = "系统"
            sender_avatar = "/avatars/system.png"
            actual_sender_id = "system"
        else:
            # chat类型：智能聊天消息（用户发送）
            sender_obj = getattr(message, 'sender', None)
            if sender_obj:
                sender_name = getattr(sender_obj, "username", "未知用户")
                sender_avatar = getattr(sender_obj, "avatar", None)
                actual_sender_id = sender_id or "unknown"
            else:
                sender_name = "未知用户"
                actual_sender_id = sender_id or "unknown"
        
        sender = MessageSender(
            id=actual_sender_id,
            name=sender_name,
            avatar=sender_avatar,
            type=sender_type
        )
        
        # 处理消息内容 - 支持统一的结构化JSON内容
        content = getattr(message, 'content', {})
        message_type = getattr(message, 'type', 'text')
        
        # 调试日志：记录模型转换过程
        # logger.debug(f"MessageInfo.from_model - 转换前: message_id={getattr(message, 'id', 'unknown')}, type={message_type}, raw_content={content}")
        
        # 确保content是字典格式
        if not isinstance(content, dict):
            content = {"text": str(content)} if content else {"text": ""}
            message_type = 'text'
        
        # 向后兼容：如果系统消息使用event_type，转换为system_event_type
        if message_type == 'system' and 'event_type' in content and 'system_event_type' not in content:
            content['system_event_type'] = content.pop('event_type')
        
        # 获取其他字段
        reactions = getattr(message, 'reactions', None)
        extra_metadata = getattr(message, 'extra_metadata', None)
        
        result = MessageInfo(
            id=getattr(message, 'id', ''),
            conversation_id=getattr(message, 'conversation_id', ''),
            content=content,
            type=message_type,
            sender=sender,
            timestamp=getattr(message, 'timestamp', datetime.now()),
            is_read=getattr(message, 'is_read', False),
            is_important=getattr(message, 'is_important', False),
            reply_to_message_id=getattr(message, 'reply_to_message_id', None),
            reactions=reactions,
            extra_metadata=extra_metadata
        )
        
        # 调试日志：记录转换后的结果
        # logger.debug(f"MessageInfo.from_model - 转换后: message_id={result.id}, content={result.content}")
        
        return result


# ===== 便利函数用于创建不同类型的消息 =====

def create_text_message_content(text: str) -> Dict[str, Any]:
    """创建文本消息内容"""
    return {"text": text}


def create_media_message_content(
    media_url: str,
    media_name: str,
    mime_type: str,
    size_bytes: int,
    text: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """创建媒体消息内容"""
    return {
        "text": text,
        "media_info": {
            "url": media_url,
            "name": media_name,
            "mime_type": mime_type,
            "size_bytes": size_bytes,
            "metadata": metadata or {}
        }
    }


def create_system_event_content(
    event_type: str,
    status: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """创建系统事件内容"""
    return {
        "system_event_type": event_type,
        "status": status,
        **kwargs
    }




def create_service_recommendation_content(
    services: List[Dict[str, Any]],
    title: str = "推荐服务"
) -> Dict[str, Any]:
    """创建服务推荐卡片内容"""
    return {
        "card_type": "service_recommendation",
        "title": title,
        "data": {"services": services},
        "actions": {
            "primary": {
                "text": "查看详情",
                "action": "view_services"
            }
        }
    }


class ConversationBase(BaseModel):
    """会话基础模型"""
    title: str
    chat_mode: str = "single"  # 会话模式：single, group
    owner_id: str  # 会话所有者
    tag: str = "chat"  # 会话标签：chat, consultation


class ConversationCreate(ConversationBase):
    """创建会话的请求模型"""
    pass


class ConversationInfo(ConversationBase):
    """会话完整模型"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "conv_123456",
                "title": "咨询会话",
                "customer_id": "usr_123456",
                "created_at": "2025-05-21T14:37:57.708339",
                "updated_at": "2025-05-21T14:37:57.708339",
                "is_active": True,
                "chat_mode": "single",
                "tag": "consultation",
                "is_pinned": False,
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
    is_archived: bool = False
    
    # 个人化字段（从 ConversationParticipant 获取）
    is_pinned: bool = False
    pinned_at: Optional[datetime] = None
    message_count: int = 0
    unread_count: int = 0
    last_message_at: Optional[datetime] = None
    
    # 关联信息
    owner: Optional[dict] = Field(None, description="会话所有者信息")

    @staticmethod
    def from_model(conversation, last_message=None, participant=None, unread_count=None):
        """从数据库模型转换为Schema模型
        
        Args:
            conversation: Conversation 模型实例
            last_message: 最后一条消息（可选）
            participant: ConversationParticipant 模型实例（可选，用于获取个人化字段）
            unread_count: 未读消息数（可选，兼容旧代码，优先使用 participant.unread_count）
        """
        if not conversation:
            return None
        
        # 获取会话所有者信息
        owner_obj = getattr(conversation, 'owner', None)
        owner_info = None
        if owner_obj:
            owner_info = {
                "id": getattr(owner_obj, 'id', ''),
                "username": getattr(owner_obj, 'username', '未知用户'),
                "email": getattr(owner_obj, 'email', ''),
                "avatar": getattr(owner_obj, 'avatar', None)
            }
        
        # 从 participant 获取个人化字段
        is_pinned = False
        pinned_at = None
        message_count = 0
        participant_unread_count = 0
        last_message_at = None
        
        if participant:
            is_pinned = getattr(participant, 'is_pinned', False)
            pinned_at = getattr(participant, 'pinned_at', None)
            message_count = getattr(participant, 'message_count', 0)
            participant_unread_count = getattr(participant, 'unread_count', 0)
            last_message_at = getattr(participant, 'last_message_at', None)
        
        # 兼容旧代码：如果没有 participant 但有 unread_count 参数
        if unread_count is not None and participant is None:
            participant_unread_count = unread_count
        
        # 转换最后一条消息
        last_message_info = None
        if last_message:
            last_message_info = MessageInfo.from_model(last_message)
        
        return ConversationInfo(
            id=getattr(conversation, 'id', ''),
            title=getattr(conversation, 'title', ''),
            chat_mode=getattr(conversation, 'chat_mode', 'single'),
            tag=getattr(conversation, 'tag', 'chat'),
            owner_id=getattr(conversation, 'owner_id', ''),
            created_at=getattr(conversation, 'created_at', datetime.now()),
            updated_at=getattr(conversation, 'updated_at', datetime.now()),
            is_active=getattr(conversation, 'is_active', True),
            is_archived=getattr(conversation, 'is_archived', False),
            is_pinned=is_pinned,
            pinned_at=pinned_at,
            message_count=message_count,
            unread_count=participant_unread_count,
            last_message_at=last_message_at,
            owner=owner_info,
            last_message=last_message_info
        )