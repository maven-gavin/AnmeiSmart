"""
聊天领域Schema
包含消息、会话等聊天相关的数据模型

支持统一消息模型的四种类型：
- text: 纯文本消息
- media: 媒体文件消息（图片、语音、视频、文档等）
- system: 系统事件消息（如用户加入、接管状态等）
- structured: 结构化卡片消息（预约确认、服务推荐等）
"""
from datetime import datetime
from typing import Optional, List, Literal, Dict, Any, Union
from pydantic import BaseModel, ConfigDict, Field


class MessageSender(BaseModel):
    """消息发送者信息"""
    id: str
    name: str
    avatar: Optional[str] = None
    type: Literal["customer", "consultant", "doctor", "ai", "system"]


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


class AppointmentCardData(BaseModel):
    """预约确认卡片数据结构"""
    appointment_id: str
    service_name: str  # 服务名称：如"面部深层清洁护理"
    consultant_name: str  # 顾问姓名
    consultant_avatar: Optional[str] = None  # 顾问头像
    scheduled_time: str  # 预约时间 ISO string
    duration_minutes: int  # 服务时长（分钟）
    price: float  # 价格
    location: str  # 地点
    status: Literal["pending", "confirmed", "cancelled"]  # 预约状态
    notes: Optional[str] = None  # 备注


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
    card_type: Literal["appointment_confirmation", "service_recommendation", "consultation_summary", "custom"]
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
    sender_type: Literal["customer", "consultant", "doctor", "ai", "system"]
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
        sender_id = getattr(message, 'sender_id', None) or "system"
        sender_type = getattr(message, 'sender_type', 'system')
        
        # 构建sender对象
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
        
        # 处理消息内容 - 支持统一的结构化JSON内容
        content = getattr(message, 'content', {})
        message_type = getattr(message, 'type', 'text')
        
        # 确保content是字典格式
        if not isinstance(content, dict):
            content = {"text": str(content)} if content else {"text": ""}
            message_type = 'text'
        
        # 获取其他字段
        reactions = getattr(message, 'reactions', None)
        extra_metadata = getattr(message, 'extra_metadata', None)
        
        return MessageInfo(
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


def create_appointment_card_content(
    appointment_data: AppointmentCardData,
    title: str = "预约确认",
    subtitle: Optional[str] = None
) -> Dict[str, Any]:
    """创建预约确认卡片内容"""
    return {
        "card_type": "appointment_confirmation",
        "title": title,
        "subtitle": subtitle,
        "data": appointment_data.model_dump(),
        "actions": {
            "primary": {
                "text": "确认预约",
                "action": "confirm_appointment",
                "data": {"appointment_id": appointment_data.appointment_id}
            },
            "secondary": {
                "text": "重新安排",
                "action": "reschedule",
                "data": {"appointment_id": appointment_data.appointment_id}
            }
        }
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
    customer_id: str
    is_ai_controlled: bool = True


class ConversationCreate(ConversationBase):
    """创建会话的请求模型"""
    consultation_type: Optional[str] = None


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
        """从数据库模型转换为Schema模型"""
        if not conversation:
            return None
        
        # 获取客户信息
        customer_obj = getattr(conversation, 'customer', None)
        customer_info = None
        if customer_obj:
            customer_info = {
                "id": getattr(customer_obj, 'id', ''),
                "username": getattr(customer_obj, 'username', '未知用户'),
                "email": getattr(customer_obj, 'email', ''),
                "avatar": getattr(customer_obj, 'avatar', None)
            }
        
        # 转换最后一条消息
        last_message_info = None
        if last_message:
            last_message_info = MessageInfo.from_model(last_message)
        
        return ConversationInfo(
            id=getattr(conversation, 'id', ''),
            title=getattr(conversation, 'title', ''),
            customer_id=getattr(conversation, 'customer_id', ''),
            created_at=getattr(conversation, 'created_at', datetime.now()),
            updated_at=getattr(conversation, 'updated_at', datetime.now()),
            is_active=getattr(conversation, 'is_active', True),
            is_ai_controlled=getattr(conversation, 'is_ai_controlled', True),
            customer=customer_info,
            last_message=last_message_info
        )