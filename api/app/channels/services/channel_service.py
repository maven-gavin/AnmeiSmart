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
            
            # 3. 根据消息类型创建消息
            if channel_message.message_type == "text":
                message = self.chat_service.create_text_message(
                    conversation_id=conversation.id,
                    sender_id=channel_message.channel_user_id,  # TODO: 需要映射到系统用户ID
                    content=channel_message.content.get("text", ""),
                    sender_type="user"
                )
            elif channel_message.message_type == "media":
                media_info = channel_message.content.get("media_info", {})
                message = self.chat_service.create_media_message_with_details(
                    conversation_id=conversation.id,
                    sender_id=channel_message.channel_user_id,
                    media_url=media_info.get("url", ""),
                    media_name=media_info.get("name"),
                    mime_type=media_info.get("mime_type"),
                    size_bytes=media_info.get("size_bytes"),
                    text=channel_message.content.get("text"),
                    metadata=channel_message.extra_data or {}
                )
            else:
                logger.warning(f"不支持的消息类型: {channel_message.message_type}")
                return None
            
            # 4. 在 extra_metadata 中存储渠道信息
            if not message.extra_metadata:
                message.extra_metadata = {}
            
            message.extra_metadata["channel"] = {
                "type": channel_message.channel_type,
                "channel_message_id": channel_message.channel_message_id,
                "channel_user_id": channel_message.channel_user_id
            }
            
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
        # TODO: 实现会话查找或创建逻辑
        # 需要考虑：
        # 1. 根据渠道用户ID查找已有会话
        # 2. 如果没有，创建新会话
        # 3. 会话标题可以从渠道用户信息获取
        
        # 临时实现：创建新会话
        from app.chat.models.chat import Conversation
        from app.common.deps.uuid_utils import conversation_id
        
        conversation = Conversation(
            id=conversation_id(),
            title=f"{channel_message.channel_type} - {channel_message.channel_user_id}",
            owner_id=channel_message.channel_user_id,  # TODO: 需要映射到系统用户ID
            chat_mode="single",
            tag="channel",
            extra_metadata={
                "channel_type": channel_message.channel_type,
                "channel_user_id": channel_message.channel_user_id
            }
        )
        
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        
        return conversation

