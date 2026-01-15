"""
聊天API端点
"""
import logging
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.identity_access.deps import get_current_user
from app.identity_access.models.user import User
from app.chat.schemas.chat import (
    ConversationCreate,
    ConversationInfo,
    MessageCreateRequest,
    MessageInfo,
    CreateTextMessageRequest,
    CreateMediaMessageRequest,
    CreateSystemEventRequest,
    CreateStructuredMessageRequest,
    ConversationParticipantInfo,
    ConversationParticipantCreate,
)
from app.core.api import (
    BusinessException, 
    SystemException,
    ApiResponse, 
    PaginatedRecords,
    ErrorCode
)

# 导入服务层
from app.chat.services.chat_service import ChatService
from app.channels.services.channel_service import ChannelService
from app.channels.deps.channel_deps import get_channel_service
from app.chat.deps.chat import get_chat_service
from app.chat.models.chat import Conversation, Message
from app.customer.services.customer_insight_pipeline import enqueue_customer_insight_job

# 导入事件总线
from app.core.websocket.events import event_bus, EventTypes
from app.identity_access.deps.permission_deps import get_user_primary_role

logger = logging.getLogger(__name__)

router = APIRouter()


# ============ HTTP API 端点 ============

@router.post("/conversations", response_model=ApiResponse[ConversationInfo], status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_in: ConversationCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """创建新会话"""
    try:
        conversation = chat_service.create_conversation(
            title=conversation_in.title,
            owner_id=str(current_user.id),
            chat_mode=conversation_in.chat_mode or "single",
            tag=conversation_in.tag or "chat"
        )
        return ApiResponse.success(conversation)
        
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"创建会话失败: {e}", exc_info=True)
        raise SystemException("创建会话失败")


@router.get("/conversations", response_model=ApiResponse[PaginatedRecords[ConversationInfo]])
async def get_conversations(
    search: Optional[str] = None,
    unassigned_only: bool = Query(False, description="是否仅获取未分配的会话"),
    customer_id: Optional[str] = Query(None, description="按客户ID过滤会话"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """根据查询条件获取用户参与的会话列表"""
    logger.info(f"端点：开始获取会话列表 - user_id={current_user.id}, unassigned_only={unassigned_only}, skip={skip}, limit={limit}")
    
    try:
        if customer_id:
            role = get_user_primary_role(current_user)
            if role == "customer" and str(customer_id) != str(current_user.id):
                raise BusinessException(
                    "无权查询其他客户会话",
                    code=ErrorCode.PERMISSION_DENIED,
                    status_code=status.HTTP_403_FORBIDDEN,
                )

        paginated_records = chat_service.get_conversations(
            user_id=str(current_user.id),
            user_role=None,  # 不再需要角色映射，sender_type统一为chat
            customer_id=customer_id,
            skip=skip,
            limit=limit,
            search=search,
            unassigned_only=unassigned_only
        )
        return ApiResponse.success(data=paginated_records)
        
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}", exc_info=True)
        raise SystemException("获取会话列表失败")


@router.get("/conversations/{conversation_id}", response_model=ApiResponse[ConversationInfo])
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取指定会话"""
    try:
        conversation = chat_service.get_conversation(
            conversation_id=conversation_id,
            user_id=str(current_user.id)
        )
        
        if not conversation:
            raise BusinessException(
                "会话不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return ApiResponse.success(conversation)
        
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"获取会话失败: {e}", exc_info=True)
        raise SystemException("获取会话失败")


@router.get(
    "/conversations/{conversation_id}/participants",
    response_model=ApiResponse[List[ConversationParticipantInfo]]
)
async def get_conversation_participants(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取会话参与者列表（owner + 成员，来自 conversation_participants 表）"""
    try:
        # 先检查是否有访问会话的权限
        can_access = await chat_service.can_access_conversation(
            conversation_id=conversation_id,
            user_id=str(current_user.id)
        )

        if not can_access:
            raise BusinessException(
                "无权访问此会话",
                code=ErrorCode.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN
            )

        participants = chat_service.get_conversation_participants(conversation_id)
        data = [ConversationParticipantInfo.from_model(p) for p in participants]

        return ApiResponse.success(data)
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"获取会话参与者失败: {e}", exc_info=True)
        raise SystemException("获取会话参与者失败")


@router.get("/conversations/{conversation_id}/messages", response_model=ApiResponse[List[MessageInfo]])
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取会话消息列表"""
    try:
        # 先检查用户是否有权限访问该会话
        conversation = chat_service.get_conversation(
            conversation_id=conversation_id,
            user_id=str(current_user.id)
        )
        if not conversation:
            raise BusinessException(
                "会话不存在",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        messages = chat_service.get_conversation_messages(
            conversation_id=conversation_id,
            limit=limit,
            offset=offset
        )
        return ApiResponse.success(messages)
        
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"获取消息列表失败: conversation_id={conversation_id}, error={str(e)}", exc_info=True)
        raise SystemException("获取消息列表失败")


@router.post("/conversations/{conversation_id}/messages", response_model=ApiResponse[MessageInfo])
async def create_message(
    conversation_id: str,
    request: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service),
    channel_service: ChannelService = Depends(get_channel_service),
):
    """创建通用消息"""
    try:
        logger.info(f"创建消息请求: conversation_id={conversation_id}, type={request.type}")
        message = chat_service.create_message(
            conversation_id=conversation_id,
            request=request,
            sender=current_user
        )

        # 渠道会话：将消息转发到对应渠道（不影响现有页面，只影响发送去向）
        conv_model = None
        try:
            conv_model = chat_service.db.query(Conversation).filter(Conversation.id == conversation_id).first()
            if conv_model and conv_model.tag == "channel":
                channel_meta = (conv_model.extra_metadata or {}).get("channel") if isinstance(conv_model.extra_metadata, dict) else None
                if isinstance(channel_meta, dict):
                    channel_type = channel_meta.get("type")
                    peer_id = channel_meta.get("peer_id")
                    if channel_type and peer_id:
                        msg_model = chat_service.db.query(Message).filter(Message.id == message.id).first()
                        if msg_model:
                            await channel_service.send_to_channel(msg_model, channel_type=channel_type, channel_user_id=peer_id)
        except Exception as e:
            logger.error(f"渠道消息转发失败: conversation_id={conversation_id}, error={e}", exc_info=True)
        
        # 广播消息
        await chat_service.broadcast_message_safe(
            conversation_id=conversation_id,
            message_info=message,
            sender_id=str(current_user.id)
        )

        # 客户发送消息后：异步触发画像洞察提取（失败不影响主流程）
        try:
            role = get_user_primary_role(current_user)
            if role == "customer":
                if not conv_model:
                    conv_model = chat_service.db.query(Conversation).filter(Conversation.id == conversation_id).first()
                # 目前仅处理站内会话（tag != channel）
                if conv_model and conv_model.tag != "channel":
                    enqueue_customer_insight_job(
                        customer_id=str(current_user.id),
                        conversation_id=conversation_id,
                        message_id=str(message.id),
                    )
        except Exception as e:
            logger.warning(
                f"触发客户画像洞察任务失败（已忽略）: conversation_id={conversation_id}, err={e}",
                exc_info=True,
            )
        
        return ApiResponse.success(message)
        
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.VALIDATION_ERROR)
    except Exception as e:
        logger.error(f"创建消息失败: conversation_id={conversation_id}, error={str(e)}", exc_info=True)
        raise SystemException(f"创建消息失败: {str(e)}")


@router.post(
    "/conversations/{conversation_id}/participants",
    response_model=ApiResponse[ConversationParticipantInfo],
    status_code=status.HTTP_201_CREATED
)
async def add_conversation_participant(
    conversation_id: str,
    request: ConversationParticipantCreate,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """添加会话参与者"""
    try:
        # 基础访问权限检查
        can_access = await chat_service.can_access_conversation(
            conversation_id=conversation_id,
            user_id=str(current_user.id)
        )

        if not can_access:
            raise BusinessException(
                "无权访问此会话",
                code=ErrorCode.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN
            )

        participant = chat_service.add_conversation_participant(
            conversation_id=conversation_id,
            current_user_id=str(current_user.id),
            user_id=request.user_id,
            role=request.role
        )

        return ApiResponse.success(ConversationParticipantInfo.from_model(participant))
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"添加会话参与者失败: {e}", exc_info=True)
        raise SystemException("添加会话参与者失败")


@router.post("/conversations/{conversation_id}/messages/text", response_model=ApiResponse[MessageInfo])
async def create_text_message(
    conversation_id: str,
    request: CreateTextMessageRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """创建文本消息"""
    try:
        message = chat_service.create_text_message_from_request(
            conversation_id=conversation_id,
            request=request,
            sender=current_user
        )
        
        # 广播消息
        await chat_service.broadcast_message_safe(
            conversation_id=conversation_id,
            message_info=message,
            sender_id=str(current_user.id)
        )
        
        return ApiResponse.success(message)
        
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.VALIDATION_ERROR)
    except Exception as e:
        logger.error(f"创建文本消息失败: {e}", exc_info=True)
        raise SystemException("创建文本消息失败")


@router.post("/conversations/{conversation_id}/messages/media", response_model=ApiResponse[MessageInfo])
async def create_media_message(
    conversation_id: str,
    request: CreateMediaMessageRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """创建媒体消息"""
    try:
        message = chat_service.create_media_message_from_request(
            conversation_id=conversation_id,
            request=request,
            sender=current_user
        )
        
        # 广播消息
        await chat_service.broadcast_message_safe(
            conversation_id=conversation_id,
            message_info=message,
            sender_id=str(current_user.id)
        )
        
        return ApiResponse.success(message)
        
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.VALIDATION_ERROR)
    except Exception as e:
        logger.error(f"创建媒体消息失败: {e}", exc_info=True)
        raise SystemException("创建媒体消息失败")


@router.post("/conversations/{conversation_id}/messages/system", response_model=ApiResponse[MessageInfo])
async def create_system_event_message(
    conversation_id: str,
    request: CreateSystemEventRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """创建系统事件消息"""
    try:
        message = chat_service.create_system_event_message(
            conversation_id=conversation_id,
            request=request,
            sender=current_user
        )
        
        # 广播消息
        await chat_service.broadcast_message_safe(
            conversation_id=conversation_id,
            message_info=message,
            sender_id=str(current_user.id)
        )
        
        return ApiResponse.success(message)
        
    except PermissionError:
        raise BusinessException(
            "只有管理员可以创建系统事件消息", 
            code=ErrorCode.PERMISSION_DENIED,
            status_code=status.HTTP_403_FORBIDDEN
        )
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.VALIDATION_ERROR)
    except Exception as e:
        logger.error(f"创建系统事件消息失败: {e}", exc_info=True)
        raise SystemException("创建系统事件消息失败")


@router.post("/conversations/{conversation_id}/messages/structured", response_model=ApiResponse[MessageInfo])
async def create_structured_message(
    conversation_id: str,
    request: CreateStructuredMessageRequest,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """创建结构化消息"""
    try:
        message = chat_service.create_structured_message(
            conversation_id=conversation_id,
            request=request,
            sender=current_user
        )
        
        # 广播消息
        await chat_service.broadcast_message_safe(
            conversation_id=conversation_id,
            message_info=message,
            sender_id=str(current_user.id)
        )
        
        return ApiResponse.success(message)
        
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.VALIDATION_ERROR)
    except Exception as e:
        logger.error(f"创建结构化消息失败: {e}", exc_info=True)
        raise SystemException("创建结构化消息失败")


@router.delete(
    "/conversations/{conversation_id}/participants/{participant_id}",
    response_model=ApiResponse[bool]
)
async def remove_conversation_participant(
    conversation_id: str,
    participant_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """移除会话参与者（逻辑删除）"""
    try:
        can_access = await chat_service.can_access_conversation(
            conversation_id=conversation_id,
            user_id=str(current_user.id)
        )

        if not can_access:
            raise BusinessException(
                "无权访问此会话",
                code=ErrorCode.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN
            )

        chat_service.remove_conversation_participant(
            conversation_id=conversation_id,
            current_user_id=str(current_user.id),
            participant_id=participant_id
        )

        return ApiResponse.success(True)
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"移除会话参与者失败: {e}", exc_info=True)
        raise SystemException("移除会话参与者失败")


@router.patch("/conversations/{conversation_id}/read", response_model=ApiResponse[Dict[str, int]])
async def mark_conversation_as_read(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """标记会话中所有未读消息为已读"""
    try:
        count = chat_service.mark_messages_as_read(
            conversation_id=conversation_id,
            user_id=str(current_user.id)
        )
        return ApiResponse.success({"count": count})
    except Exception as e:
        logger.error(f"标记会话已读失败: {e}", exc_info=True)
        raise SystemException("标记会话已读失败")


@router.patch("/messages/{message_id}/read", response_model=ApiResponse[Dict[str, str]])
async def mark_message_as_read(
    message_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """标记消息为已读"""
    try:
        success = chat_service.mark_message_as_read(message_id)
        if not success:
            raise BusinessException(
                "消息不存在", 
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return ApiResponse.success({"message": "消息已标记为已读"})
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"标记消息已读失败: {e}", exc_info=True)
        raise SystemException("标记消息已读失败")


@router.patch("/conversations/{conversation_id}/messages/{message_id}/important", response_model=ApiResponse[Dict[str, str]])
async def mark_message_as_important(
    conversation_id: str,
    message_id: str,
    request_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """标记消息为重点"""
    try:
        is_important = request_data.get("is_important", False)
        
        success = chat_service.mark_message_as_important(
            message_id=message_id,
            is_important=is_important
        )
        
        if success:
            return ApiResponse.success({"message": f"消息已{'标记为重点' if is_important else '取消重点标记'}"})
        else:
            raise BusinessException(
                "消息不存在", 
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
    except PermissionError:
        raise BusinessException(
            "无权操作此会话", 
            code=ErrorCode.PERMISSION_DENIED,
            status_code=status.HTTP_403_FORBIDDEN
        )
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.VALIDATION_ERROR)
    except Exception as e:
        logger.error(f"标记消息重点状态失败: {e}", exc_info=True)
        raise SystemException("标记消息重点状态失败")


@router.get("/conversations/{conversation_id}/summary", response_model=ApiResponse[ConversationInfo])
async def get_conversation_summary(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取会话摘要"""
    try:
        # 暂时返回会话信息作为摘要，后续可以添加专门的摘要功能
        summary = chat_service.get_conversation_by_id(
            conversation_id=conversation_id,
            user_id=str(current_user.id),
            user_role=None  # 不再需要角色映射，sender_type统一为chat
        )
        
        if not summary:
            raise BusinessException(
                "会话不存在", 
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return ApiResponse.success(summary)
        
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"获取会话摘要失败: {e}", exc_info=True)
        raise SystemException("获取会话摘要失败")


@router.patch("/conversations/{conversation_id}", response_model=ApiResponse[ConversationInfo])
async def update_conversation(
    conversation_id: str,
    update_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """更新会话信息"""
    try:
        updated_conversation = chat_service.update_conversation(
            conversation_id=conversation_id,
            user_id=str(current_user.id),
            updates=update_data
        )
        
        if not updated_conversation:
            raise BusinessException(
                "会话不存在", 
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        return ApiResponse.success(updated_conversation)
        
    except PermissionError:
        raise BusinessException(
            "无权修改此会话", 
            code=ErrorCode.PERMISSION_DENIED,
            status_code=status.HTTP_403_FORBIDDEN
        )
    except Exception as e:
        logger.error(f"更新会话失败: {e}", exc_info=True)
        raise SystemException("更新会话失败")


@router.get("/conversations/{conversation_id}/takeover-status", response_model=ApiResponse[Dict[str, Any]])
async def get_takeover_status(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """获取当前用户的接管状态"""
    try:
        # 检查用户是否有权限访问该会话
        can_access = await chat_service.can_access_conversation(
            conversation_id=conversation_id,
            user_id=str(current_user.id)
        )
        
        if not can_access:
            raise BusinessException(
                "无权访问此会话",
                code=ErrorCode.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # 获取接管状态
        takeover_status = chat_service.get_participant_takeover_status(
            conversation_id=conversation_id,
            user_id=str(current_user.id)
        )
        
        # 如果参与者不存在，返回默认值
        final_status = takeover_status or "no_takeover"
        
        return ApiResponse.success({
            "conversation_id": conversation_id,
            "user_id": str(current_user.id),
            "takeover_status": final_status
        })
        
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"获取接管状态失败: {e}", exc_info=True)
        raise SystemException("获取接管状态失败")


@router.patch("/conversations/{conversation_id}/takeover-status", response_model=ApiResponse[Dict[str, Any]])
async def set_takeover_status(
    conversation_id: str,
    takeover_status: str = Query(..., description="接管状态: full_takeover, semi_takeover, no_takeover"),
    current_user: User = Depends(get_current_user),
    chat_service: ChatService = Depends(get_chat_service)
):
    """设置参与者的接管状态 - 支持三种状态"""
    try:
        # 验证接管状态值
        valid_statuses = ["full_takeover", "semi_takeover", "no_takeover"]
        if takeover_status not in valid_statuses:
            raise BusinessException(
                f"无效的接管状态: {takeover_status}，有效值: {valid_statuses}",
                code=ErrorCode.INVALID_INPUT,
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # 检查用户是否有权限访问该会话
        can_access = await chat_service.can_access_conversation(
            conversation_id=conversation_id,
            user_id=str(current_user.id)
        )
        
        if not can_access:
            raise BusinessException(
                "无权访问此会话",
                code=ErrorCode.PERMISSION_DENIED,
                status_code=status.HTTP_403_FORBIDDEN
            )
        
        # 设置接管状态
        participant = chat_service.set_participant_takeover_status(
            conversation_id=conversation_id,
            user_id=str(current_user.id),
            takeover_status=takeover_status
        )
        
        # 确保 takeover_status 不为 None
        final_status = participant.takeover_status or takeover_status
        
        logger.info(f"设置接管状态成功: conversation_id={conversation_id}, user_id={current_user.id}, takeover_status={final_status}")
        
        return ApiResponse.success({
            "conversation_id": conversation_id,
            "user_id": str(current_user.id),
            "takeover_status": final_status
        })
        
    except BusinessException:
        raise
    except Exception as e:
        logger.error(f"设置接管状态失败: {e}", exc_info=True)
        raise SystemException("设置接管状态失败")


# ============ 事件处理器注册 ============

# 在模块加载时注册事件处理器
def setup_chat_event_handlers():
    """设置聊天相关的事件处理器"""
    
    async def handle_message_sent(event):
        """处理消息发送事件"""
        # 这里可以添加额外的业务逻辑
        # 例如：记录日志、发送通知等
        logger.info(f"消息已发送: conversation_id={event.conversation_id}")
    
    async def handle_ai_response(event):
        """处理AI回复事件"""
        logger.info(f"AI回复已生成: conversation_id={event.conversation_id}")
    
    # 注册事件处理器
    event_bus.subscribe_async(EventTypes.CHAT_MESSAGE_SENT, handle_message_sent)
    event_bus.subscribe_async(EventTypes.AI_RESPONSE_GENERATED, handle_ai_response)


# 初始化事件处理器
setup_chat_event_handlers() 