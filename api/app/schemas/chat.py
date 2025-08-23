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
from pydantic import BaseModel, ConfigDict, Field, validator, field_validator
from enum import Enum


class MessageSender(BaseModel):
    """消息发送者信息"""
    id: str
    name: str
    avatar: Optional[str] = None
    type: Literal["customer", "consultant", "doctor", "ai", "system", "digital_human"]


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
        sender_type = getattr(message, 'sender_type', 'system')
        
        # 构建sender对象
        sender_name = "系统"
        sender_avatar = None
        actual_sender_id = "system"
        
        if sender_type == "system":
            sender_name = "系统"
            sender_avatar = "/avatars/system.png"
            actual_sender_id = "system"
        elif sender_type == "digital_human":
            # 数字人发送者
            digital_human_obj = getattr(message, 'sender_digital_human', None)
            if digital_human_obj:
                sender_name = getattr(digital_human_obj, "name", "数字人助手")
                sender_avatar = getattr(digital_human_obj, "avatar", "/avatars/ai.png")
                actual_sender_id = sender_digital_human_id or "digital_human"
            else:
                sender_name = "数字人助手"
                sender_avatar = "/avatars/ai.png"
                actual_sender_id = sender_digital_human_id or "digital_human"
        elif sender_type == "ai":
            sender_name = "AI助手"
            sender_avatar = "/avatars/ai.png"
            actual_sender_id = sender_id or "ai"
        else:
            # 用户发送者
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
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"MessageInfo.from_model - 转换前: message_id={getattr(message, 'id', 'unknown')}, type={message_type}, raw_content={content}")
        
        # 确保content是字典格式
        if not isinstance(content, dict):
            content = {"text": str(content)} if content else {"text": ""}
            message_type = 'text'
        
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
        logger.info(f"MessageInfo.from_model - 转换后: message_id={result.id}, content={result.content}")
        
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
    
    # 新增字段
    is_pinned: bool = False
    pinned_at: Optional[datetime] = None
    first_participant_id: Optional[str] = None
    
    # 统计信息
    message_count: int = 0
    unread_count: int = 0
    last_message_at: Optional[datetime] = None
    
    # 关联信息
    owner: Optional[dict] = Field(None, description="会话所有者信息")
    first_participant: Optional[dict] = Field(None, description="第一个参与者信息")

    @staticmethod
    def from_model(conversation, last_message=None, unread_count=0):
        """从数据库模型转换为Schema模型"""
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
        
        # 获取第一个参与者信息
        first_participant_obj = getattr(conversation, 'first_participant', None)
        first_participant_info = None
        if first_participant_obj:
            first_participant_info = {
                "id": getattr(first_participant_obj, 'id', ''),
                "username": getattr(first_participant_obj, 'username', '未知用户'),
                "email": getattr(first_participant_obj, 'email', ''),
                "avatar": getattr(first_participant_obj, 'avatar', None)
            }
        
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
            is_pinned=getattr(conversation, 'is_pinned', False),
            pinned_at=getattr(conversation, 'pinned_at', None),
            first_participant_id=getattr(conversation, 'first_participant_id', None),
            message_count=getattr(conversation, 'message_count', 0),
            unread_count=getattr(conversation, 'unread_count', 0),
            last_message_at=getattr(conversation, 'last_message_at', None),
            owner=owner_info,
            first_participant=first_participant_info,
            last_message=last_message_info
        )


# 咨询类型枚举
class ConsultationType(str, Enum):
    initial = "initial"
    follow_up = "follow_up"
    emergency = "emergency"
    specialized = "specialized"
    other = "other"


# 咨询总结基础信息
class ConsultationSummaryBasicInfo(BaseModel):
    start_time: datetime = Field(..., description="咨询开始时间")
    end_time: datetime = Field(..., description="咨询结束时间")
    duration_minutes: int = Field(..., description="咨询时长（分钟）")
    type: ConsultationType = Field(..., description="咨询类型")
    consultant_id: str = Field(..., description="顾问ID")
    customer_id: str = Field(..., description="客户ID")


# 完整的咨询总结
class ConsultationSummary(BaseModel):
    basic_info: ConsultationSummaryBasicInfo = Field(..., description="基础信息")
    main_issues: List[str] = Field(default=[], description="主要问题")
    solutions: List[str] = Field(default=[], description="解决方案")
    follow_up_plan: List[str] = Field(default=[], description="跟进计划")
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5, description="满意度评分（1-5分）")
    additional_notes: Optional[str] = Field(None, description="补充备注")
    tags: List[str] = Field(default=[], description="标签")
    ai_generated: bool = Field(default=False, description="是否AI生成")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    version: int = Field(default=1, description="版本号")

    @field_validator('satisfaction_rating')
    @classmethod
    def validate_satisfaction_rating(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('满意度评分必须在1-5之间')
        return v
    
    @classmethod
    def create_summary(cls, basic_info: ConsultationSummaryBasicInfo, 
                      main_issues: List[str] = None, solutions: List[str] = None,
                      follow_up_plan: List[str] = None, satisfaction_rating: int = None,
                      additional_notes: str = None, tags: List[str] = None,
                      ai_generated: bool = False) -> "ConsultationSummary":
        """统一的工厂方法创建咨询总结"""
        return cls(
            basic_info=basic_info,
            main_issues=main_issues or [],
            solutions=solutions or [],
            follow_up_plan=follow_up_plan or [],
            satisfaction_rating=satisfaction_rating,
            additional_notes=additional_notes,
            tags=tags or [],
            ai_generated=ai_generated,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            version=1
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConsultationSummary":
        """从字典数据重构ConsultationSummary对象"""
        # 处理基础信息
        basic_info_data = data.get('basic_info', {})
        if isinstance(basic_info_data.get('start_time'), str):
            basic_info_data['start_time'] = datetime.fromisoformat(basic_info_data['start_time'].replace('Z', '+00:00'))
        if isinstance(basic_info_data.get('end_time'), str):
            basic_info_data['end_time'] = datetime.fromisoformat(basic_info_data['end_time'].replace('Z', '+00:00'))
        
        # 处理时间字段
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        if isinstance(data.get('updated_at'), str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        
        data['basic_info'] = ConsultationSummaryBasicInfo(**basic_info_data)
        return cls(**data)
    
    def update_from_request(self, request) -> "ConsultationSummary":
        """根据更新请求更新咨询总结"""
        updated_data = self.model_dump()
        
        if request.main_issues is not None:
            updated_data['main_issues'] = request.main_issues
        if request.solutions is not None:
            updated_data['solutions'] = request.solutions
        if request.follow_up_plan is not None:
            updated_data['follow_up_plan'] = request.follow_up_plan
        if request.satisfaction_rating is not None:
            updated_data['satisfaction_rating'] = request.satisfaction_rating
        if request.additional_notes is not None:
            updated_data['additional_notes'] = request.additional_notes
        if request.tags is not None:
            updated_data['tags'] = request.tags
        
        updated_data['updated_at'] = datetime.utcnow()
        updated_data['version'] += 1
        
        return ConsultationSummary(**updated_data)
    
# 移除冗余方法，简化schema职责


# 创建咨询总结的请求
class CreateConsultationSummaryRequest(BaseModel):
    conversation_id: str = Field(..., description="会话ID")
    main_issues: List[str] = Field(..., description="主要问题")
    solutions: List[str] = Field(..., description="解决方案")
    follow_up_plan: List[str] = Field(default=[], description="跟进计划")
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5, description="满意度评分")
    additional_notes: Optional[str] = Field(None, description="补充备注")
    tags: List[str] = Field(default=[], description="标签")


# 更新咨询总结的请求
class UpdateConsultationSummaryRequest(BaseModel):
    main_issues: Optional[List[str]] = Field(None, description="主要问题")
    solutions: Optional[List[str]] = Field(None, description="解决方案")
    follow_up_plan: Optional[List[str]] = Field(None, description="跟进计划")
    satisfaction_rating: Optional[int] = Field(None, ge=1, le=5, description="满意度评分")
    additional_notes: Optional[str] = Field(None, description="补充备注")
    tags: Optional[List[str]] = Field(None, description="标签")


# AI生成总结的请求
class AIGenerateSummaryRequest(BaseModel):
    conversation_id: str = Field(..., description="会话ID")
    include_suggestions: bool = Field(default=True, description="是否包含建议")
    focus_areas: List[str] = Field(default=[], description="重点关注领域")


class AIGeneratedSummaryResponse(BaseModel):
    """AI生成咨询总结的响应"""
    conversation_id: str = Field(..., description="会话ID")
    main_issues: List[str] = Field(default=[], description="AI识别的主要问题")
    solutions: List[str] = Field(default=[], description="AI建议的解决方案")
    follow_up_plan: List[str] = Field(default=[], description="AI制定的跟进计划")
    satisfaction_rating: Optional[int] = Field(None, description="AI评估的满意度")
    additional_notes: Optional[str] = Field(None, description="AI生成的补充说明")
    tags: List[str] = Field(default=[], description="AI生成的标签")
    ai_confidence: Optional[float] = Field(None, description="AI生成置信度")
    
    @classmethod
    def from_ai_response(cls, ai_response: Dict[str, Any], conversation_id: str) -> "AIGeneratedSummaryResponse":
        """从AI响应创建总结数据"""
        try:
            import json
            
            # 获取AI回复内容
            content = ai_response.get("content", "")
            
            # 尝试解析JSON
            if content.strip().startswith("{"):
                summary_data = json.loads(content)
            else:
                # 如果不是JSON，创建默认结构
                summary_data = {
                    "main_issues": [content[:100] + "..." if len(content) > 100 else content],
                    "solutions": [],
                    "follow_up_plan": [],
                    "additional_notes": content,
                    "tags": ["AI生成"]
                }
            
            return cls(
                conversation_id=conversation_id,
                main_issues=summary_data.get('main_issues', []),
                solutions=summary_data.get('solutions', []),
                follow_up_plan=summary_data.get('follow_up_plan', []),
                satisfaction_rating=summary_data.get('satisfaction_rating'),
                additional_notes=summary_data.get('additional_notes'),
                tags=summary_data.get('tags', []),
                ai_confidence=ai_response.get('confidence', 0.8)  # 默认置信度
            )
            
        except Exception as e:
            # 解析失败时返回默认数据
            return cls(
                conversation_id=conversation_id,
                main_issues=["AI分析失败"],
                solutions=[],
                follow_up_plan=[],
                additional_notes=f"AI响应解析错误: {str(e)}",
                tags=["错误"],
                ai_confidence=0.0
            )


# 咨询总结响应
class ConsultationSummaryResponse(BaseModel):
    id: str = Field(..., description="会话ID")
    title: str = Field(..., description="会话标题")
    consultation_type: Optional[ConsultationType] = Field(None, description="咨询类型")
    consultation_summary: Optional[ConsultationSummary] = Field(None, description="详细总结")
    summary: Optional[str] = Field(None, description="简短摘要")
    has_summary: bool = Field(..., description="是否有总结")
    customer_name: str = Field(..., description="客户姓名")
    consultant_name: Optional[str] = Field(None, description="顾问姓名")
    created_at: datetime = Field(..., description="会话创建时间")
    updated_at: datetime = Field(..., description="最后更新时间")

    @staticmethod
    def from_model(conversation) -> "ConsultationSummaryResponse":
        """从ORM模型转换为响应Schema"""
        consultant_name = None
        if conversation.assigned_consultant:
            consultant_name = conversation.assigned_consultant.username
        
        has_summary = bool(conversation.consultation_summary)
        
        consultation_summary = None
        if conversation.consultation_summary:
            consultation_summary = ConsultationSummary(**conversation.consultation_summary)
        
        return ConsultationSummaryResponse(
            id=conversation.id,
            title=conversation.title,
            consultation_type=conversation.consultation_type,
            consultation_summary=consultation_summary,
            summary=conversation.summary,
            has_summary=has_summary,
            customer_name=conversation.owner.username if conversation.owner else "未知用户",
            consultant_name=consultant_name,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )


# 简化的咨询总结信息（用于列表显示）
class ConsultationSummaryInfo(BaseModel):
    id: str = Field(..., description="会话ID")
    title: str = Field(..., description="会话标题")
    consultation_type: Optional[str] = Field(None, description="咨询类型")
    summary_text: Optional[str] = Field(None, description="总结文本")
    has_summary: bool = Field(..., description="是否有总结")
    customer_name: str = Field(..., description="客户姓名")
    date: str = Field(..., description="日期")
    duration_minutes: Optional[int] = Field(None, description="时长")
    satisfaction_rating: Optional[int] = Field(None, description="满意度")

    @staticmethod
    def from_model(conversation) -> "ConsultationSummaryInfo":
        """从ORM模型转换为简化信息Schema"""
        has_summary = bool(conversation.consultation_summary)
        
        summary_text = None
        duration_minutes = None
        satisfaction_rating = None
        
        if conversation.consultation_summary:
            # 从详细总结中提取信息
            if conversation.consultation_summary.get('main_issues'):
                summary_text = "; ".join(conversation.consultation_summary['main_issues'][:2])
            duration_minutes = conversation.consultation_summary.get('basic_info', {}).get('duration_minutes')
            satisfaction_rating = conversation.consultation_summary.get('satisfaction_rating')
        elif conversation.summary:
            summary_text = conversation.summary[:100] + "..." if len(conversation.summary) > 100 else conversation.summary
        
        consultation_type_display = {
            'initial': '初次咨询',
            'follow_up': '复诊咨询', 
            'emergency': '紧急咨询',
            'specialized': '专项咨询',
            'other': '其他'
        }.get(conversation.consultation_type, conversation.consultation_type)
        
        return ConsultationSummaryInfo(
            id=conversation.id,
            title=conversation.title,
            consultation_type=consultation_type_display,
            summary_text=summary_text,
            has_summary=has_summary,
            customer_name=conversation.owner.username if conversation.owner else "未知用户",
            date=conversation.created_at.strftime("%Y-%m-%d"),
            duration_minutes=duration_minutes,
            satisfaction_rating=satisfaction_rating
        )