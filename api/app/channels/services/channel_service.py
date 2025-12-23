"""
渠道服务 - 统一管理所有渠道
"""
import logging
from typing import Dict, Optional, List
from sqlalchemy.orm import Session

from app.channels.interfaces import ChannelAdapter, ChannelMessage
from app.channels.models.channel_config import ChannelConfig
from app.chat.services.chat_service import ChatService
from app.chat.models.chat import Message, Conversation
from app.core.api import BusinessException, ErrorCode

logger = logging.getLogger(__name__)


class ChannelService:
    """渠道服务 - 统一管理所有渠道"""
    
    def __init__(self, db: Session, broadcasting_service=None):
        self.db = db
        self.adapters: Dict[str, ChannelAdapter] = {}
        self.chat_service = ChatService(db=db, broadcasting_service=broadcasting_service)
    
    def register_adapter(self, channel_type: str, adapter: ChannelAdapter):
        """注册渠道适配器"""
        self.adapters[channel_type] = adapter
        logger.info(f"注册渠道适配器: {channel_type}")
    
    def get_adapter(self, channel_type: str) -> Optional[ChannelAdapter]:
        """获取渠道适配器"""
        return self.adapters.get(channel_type)
    
    async def process_incoming_message(self, channel_message: ChannelMessage) -> Optional[Message]:
        """
        处理来自外部渠道的消息
        
        Args:
            channel_message: 渠道消息
            
        Returns:
            创建的消息对象
        """
        try:
            # 1. 查找或创建会话
            conversation = await self._get_or_create_conversation(channel_message)
            
            # 2. 检查消息是否已存在（去重）
            # 使用 JSON 字段查询
            from sqlalchemy import cast, String
            existing_message = self.db.query(Message).filter(
                cast(Message.extra_metadata['channel']['channel_message_id'], String) == channel_message.channel_message_id
            ).first()
            
            if existing_message:
                logger.info(f"消息已存在，跳过处理: {channel_message.channel_message_id}")
                return existing_message
            
            # 3. 准备渠道信息
            channel_metadata = {
                "type": channel_message.channel_type,
                "channel_message_id": channel_message.channel_message_id,
                "peer_id": channel_message.channel_user_id,
                "peer_name": channel_message.extra_data.get("peer_name") if channel_message.extra_data else None,
                "direction": "inbound",
            }
            
            # 合并 extra_metadata
            extra_metadata = channel_message.extra_data or {}
            if "channel" not in extra_metadata:
                extra_metadata["channel"] = channel_metadata
            else:
                extra_metadata["channel"].update(channel_metadata)
            
            # 4. 根据消息类型创建消息
            if channel_message.message_type == "text":
                message_info = self.chat_service.create_text_message(
                    conversation_id=conversation.id,
                    sender_id=None,  # 渠道入站：外部发送者不对应系统 user_id
                    content=channel_message.content.get("text", ""),
                    sender_type="user",
                    extra_metadata=extra_metadata
                )
            elif channel_message.message_type == "media":
                media_info = channel_message.content.get("media_info", {})
                message_info = self.chat_service.create_media_message_with_details(
                    conversation_id=conversation.id,
                    sender_id=None,
                    media_url=media_info.get("url", ""),
                    media_name=media_info.get("name"),
                    mime_type=media_info.get("mime_type"),
                    size_bytes=media_info.get("size_bytes"),
                    text=channel_message.content.get("text"),
                    metadata=extra_metadata
                )
            else:
                logger.warning(f"不支持的消息类型: {channel_message.message_type}")
                return None
            
            # 5. 通过 message_id 查询 ORM 对象（因为 create_* 方法返回的是 MessageInfo schema）
            message = self.db.query(Message).filter(Message.id == message_info.id).first()
            if not message:
                logger.error(f"无法找到刚创建的消息: {message_info.id}")
                return None
            
            # 6. 确保 extra_metadata 已正确设置（双重保险）
            if not message.extra_metadata or "channel" not in message.extra_metadata:
                if not message.extra_metadata:
                    message.extra_metadata = {}
                message.extra_metadata["channel"] = channel_metadata
                self.db.commit()
                self.db.refresh(message)
            
            logger.info(f"成功处理渠道消息: {channel_message.channel_message_id}")
            return message
            
        except Exception as e:
            logger.error(f"处理渠道消息失败: {e}", exc_info=True)
            self.db.rollback()
            raise
    
    async def send_to_channel(
        self, 
        message: Message, 
        channel_type: str, 
        channel_user_id: str
    ) -> bool:
        """
        发送消息到外部渠道
        
        Args:
            message: 系统消息对象
            channel_type: 渠道类型
            channel_user_id: 渠道用户ID
            
        Returns:
            是否发送成功
        """
        adapter = self.adapters.get(channel_type)
        if not adapter:
            logger.error(f"未找到渠道适配器: {channel_type}")
            return False
        
        try:
            success = await adapter.send_message(message, channel_user_id)
            if success:
                logger.info(f"成功发送消息到渠道: {channel_type}, message_id={message.id}")
            else:
                logger.warning(f"发送消息到渠道失败: {channel_type}, message_id={message.id}")
            return success
        except Exception as e:
            logger.error(f"发送消息到渠道异常: {e}", exc_info=True)
            return False
    
    async def _get_or_create_conversation(self, channel_message: ChannelMessage) -> Conversation:
        """获取或创建会话"""
        from sqlalchemy import cast, String
        from app.common.deps.uuid_utils import conversation_id
        from app.identity_access.models.user import User

        peer_id = channel_message.channel_user_id

        # 1) 查找已有渠道会话
        existing = self.db.query(Conversation).filter(
            Conversation.tag == "channel",
            cast(Conversation.extra_metadata["channel"]["type"], String) == channel_message.channel_type,
            cast(Conversation.extra_metadata["channel"]["peer_id"], String) == peer_id,
        ).first()

        if existing:
            return existing

        # 2) 选择一个可用 owner（仅用于满足外键，权限由 tag=channel 的规则控制）
        owner = self.db.query(User).order_by(User.created_at.asc()).first()
        if not owner:
            raise BusinessException("系统内没有可用用户，无法创建渠道会话", code=ErrorCode.SYSTEM_ERROR)

        title = f"{channel_message.channel_type}:{peer_id}"

        conversation = Conversation(
            id=conversation_id(),
            title=title,
            owner_id=str(owner.id),
            chat_mode="single",
            tag="channel",
            extra_metadata={
                "channel": {
                    "type": channel_message.channel_type,
                    "peer_id": peer_id,
                    "peer_name": channel_message.extra_data.get("peer_name") if channel_message.extra_data else None,
                },
                "assignment": {
                    "status": "unassigned",
                    "assignee_user_id": None,
                    "assignee_name": None,
                    "assigned_at": None,
                },
            },
        )

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

