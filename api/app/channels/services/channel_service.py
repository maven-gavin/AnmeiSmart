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
from app.common.services.file_service import FileService
from app.core.api import BusinessException, ErrorCode

logger = logging.getLogger(__name__)


class ChannelService:
    """渠道服务 - 统一管理所有渠道"""
    
    def __init__(self, db: Session, broadcasting_service=None):
        self.db = db
        self.adapters: Dict[str, ChannelAdapter] = {}
        self.broadcasting_service = broadcasting_service
        self.chat_service = ChatService(db=db, broadcasting_service=broadcasting_service)
        self.file_service = FileService(db=db)
    
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
                
                # 如果是企业微信媒体，且有MediaId，尝试下载并转存到我们的MinIO
                media_id = channel_message.extra_data.get("media_id") if channel_message.extra_data else None
                if media_id and channel_message.channel_type == "wechat_work":
                    adapter = self.get_adapter("wechat_work")
                    if adapter and hasattr(adapter, "client"):
                        logger.info(f"尝试下载并转存企业微信媒体: media_id={media_id}")
                        data = await adapter.client.download_media(media_id)
                        if data:
                            # 转存到我们的MinIO
                            # 尝试获取文件名
                            filename = media_info.get("name") or channel_message.extra_data.get("file_name") or f"wechat_{media_id}"
                            
                            # 获取 MIME 类型
                            mime_type = media_info.get("mime_type")
                            
                            upload_result = await self.file_service.upload_binary_data(
                                data=data,
                                filename=filename,
                                conversation_id=conversation.id,
                                user_id=conversation.owner_id, # 使用会话所有者作为文件归属
                                mime_type=mime_type
                            )
                            
                            # 更新 media_info 使用我们的存储信息
                            media_info["file_id"] = upload_result["file_id"]
                            media_info["name"] = upload_result["file_name"]
                            media_info["size_bytes"] = upload_result["file_size"]
                            media_info["mime_type"] = upload_result["mime_type"]
                            logger.info(f"企业微信媒体转存成功: file_id={media_info['file_id']}")
                        else:
                            logger.warning(f"下载企业微信媒体失败: media_id={media_id}")

                media_file_id = media_info.get("file_id")
                if not media_file_id:
                    logger.warning("渠道媒体消息缺少 file_id，无法创建媒体消息")
                    return None

                message_info = self.chat_service.create_media_message_with_details(
                    conversation_id=conversation.id,
                    sender_id=None,
                    media_file_id=media_file_id,
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
            
            # 7. 广播新消息到 WebSocket
            if self.broadcasting_service:
                try:
                    # 使用 message_info (Schema) 转换为字典进行广播
                    await self.broadcasting_service.broadcast_message(
                        conversation_id=conversation.id,
                        message_data=message_info.model_dump()
                    )
                    logger.info(f"成功广播渠道消息: {channel_message.channel_message_id}")
                except Exception as e:
                    logger.error(f"广播渠道消息失败: {e}", exc_info=True)
            
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
        """
        获取或创建会话
        
        根据 channel_type 和 peer_id 判断是否为同一个会话。
        如果 peer_id 和 type 相同，就认为是同一个会话。
        """
        from sqlalchemy import cast, String
        from app.common.deps.uuid_utils import conversation_id
        from app.identity_access.models.user import User

        peer_id = channel_message.channel_user_id
        channel_type = channel_message.channel_type
        
        logger.info(f"查找或创建渠道会话: channel_type={channel_type}, peer_id={peer_id}")

        # 1) 查找已有渠道会话
        # 根据 channel_type 和 peer_id 判断是否为同一个会话
        # 先尝试SQL查询（性能好），如果失败则使用Python方式查询（更可靠）
        existing = None
        
        # 方法1：使用SQL查询（需要确保extra_metadata结构正确）
        try:
            existing = self.db.query(Conversation).filter(
                Conversation.tag == "channel",
                Conversation.extra_metadata.isnot(None),
                cast(Conversation.extra_metadata["channel"]["type"], String) == channel_type,
                cast(Conversation.extra_metadata["channel"]["peer_id"], String) == peer_id,
            ).first()
        except Exception as e:
            logger.warning(f"SQL查询渠道会话失败，将使用Python方式查询: {e}")
        
        # 方法2：如果SQL查询失败或返回None，使用Python方式查询（备用方案）
        if not existing:
            try:
                all_channel_convs = self.db.query(Conversation).filter(
                    Conversation.tag == "channel",
                    Conversation.extra_metadata.isnot(None)
                ).all()
                
                for conv in all_channel_convs:
                    if conv.extra_metadata and isinstance(conv.extra_metadata, dict):
                        channel_meta = conv.extra_metadata.get("channel", {})
                        if (isinstance(channel_meta, dict) and 
                            channel_meta.get("type") == channel_type and 
                            str(channel_meta.get("peer_id")) == str(peer_id)):
                            existing = conv
                            logger.info(f"通过Python方式找到已存在的渠道会话: conversation_id={conv.id}, channel_type={channel_type}, peer_id={peer_id}")
                            break
            except Exception as e:
                logger.error(f"Python方式查询渠道会话也失败: {e}", exc_info=True)
        
        if existing:
            logger.info(f"找到已存在的渠道会话: conversation_id={existing.id}, channel_type={channel_type}, peer_id={peer_id}")
            return existing
        
        logger.info(f"未找到匹配的渠道会话，将创建新会话: channel_type={channel_type}, peer_id={peer_id}")

        # 2) 没有找到匹配的会话，创建新会话
        # 选择一个可用 owner（仅用于满足外键，权限由 tag=channel 的规则控制）
        owner = self.db.query(User).order_by(User.created_at.asc()).first()
        if not owner:
            raise BusinessException("系统内没有可用用户，无法创建渠道会话", code=ErrorCode.SYSTEM_ERROR)

        title = f"{channel_type}:{peer_id}"
        
        logger.info(f"创建新的渠道会话: title={title}, channel_type={channel_type}, peer_id={peer_id}")

        conversation = Conversation(
            id=conversation_id(),
            title=title,
            owner_id=str(owner.id),
            chat_mode="single",
            tag="channel",
            extra_metadata={
                "channel": {
                    "type": channel_type,
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
        
        logger.info(f"成功创建新的渠道会话: conversation_id={conversation.id}, title={title}")
        return conversation

