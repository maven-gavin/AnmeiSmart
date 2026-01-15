"""
渠道服务 - 统一管理所有渠道
"""
import logging
import hashlib
import secrets
from typing import Dict, Optional, List
from sqlalchemy.orm import Session

from app.channels.interfaces import ChannelAdapter, ChannelMessage
from app.channels.models.channel_config import ChannelConfig
from app.channels.models.channel_identity import ChannelIdentity
from app.chat.services.chat_service import ChatService
from app.chat.models.chat import Message, Conversation
from app.common.services.file_service import FileService
from app.core.api import BusinessException, ErrorCode
from app.customer.services.customer_insight_pipeline import enqueue_customer_insight_job

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
            # 0. 渠道身份归一：channel_type + peer_id -> customer(User)
            customer_user_id, customer_display_name = self._resolve_or_create_customer_user(channel_message)

            # 1. 查找或创建会话
            conversation = await self._get_or_create_conversation(
                channel_message=channel_message,
                owner_user_id=customer_user_id,
                owner_display_name=customer_display_name,
            )
            
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
            direction = "inbound"
            if channel_message.extra_data and isinstance(channel_message.extra_data, dict):
                direction = channel_message.extra_data.get("direction") or direction

            channel_metadata = {
                "type": channel_message.channel_type,
                "channel_message_id": channel_message.channel_message_id,
                "peer_id": channel_message.channel_user_id,
                "peer_name": channel_message.extra_data.get("peer_name") if channel_message.extra_data else None,
                "customer_user_id": customer_user_id,
                "direction": direction,
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
                
                # 会话存档媒体：优先使用 sdkfileid 下载并转存
                sdkfileid = media_info.get("sdkfileid")
                if sdkfileid and channel_message.channel_type == "wechat_work_contact":
                    from app.channels.services.wechat_work_archive_service import WeChatWorkArchiveService

                    archive_service = WeChatWorkArchiveService(db=self.db)
                    data = await archive_service.download_media(sdkfileid=str(sdkfileid))
                    filename = media_info.get("name") or f"media_{sdkfileid}"
                    mime_type = media_info.get("mime_type")
                    upload_result = await self.file_service.upload_binary_data(
                        data=data,
                        filename=filename,
                        conversation_id=conversation.id,
                        user_id=conversation.owner_id,
                        mime_type=mime_type,
                    )
                    media_info["file_id"] = upload_result["file_id"]
                    media_info["name"] = upload_result["file_name"]
                    media_info["size_bytes"] = upload_result["file_size"]
                    media_info["mime_type"] = upload_result["mime_type"]

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

                # 会话内容存档媒体：sdkfileid -> 下载 -> 转存
                if channel_message.channel_type == "wechat_work_contact" and not media_info.get("file_id"):
                    sdkfileid = media_info.get("sdkfileid")
                    if sdkfileid:
                        from app.channels.services.wechat_work_archive_service import WeChatWorkArchiveService

                        archive_service = WeChatWorkArchiveService(db=self.db)
                        data = await archive_service.download_media(sdkfileid=str(sdkfileid))
                        if data:
                            filename = media_info.get("name") or f"wechat_{sdkfileid}"
                            mime_type = media_info.get("mime_type")
                            upload_result = await self.file_service.upload_binary_data(
                                data=data,
                                filename=filename,
                                conversation_id=str(conversation.id),
                                user_id=str(conversation.owner_id),
                                mime_type=mime_type,
                            )
                            media_info["file_id"] = upload_result["file_id"]
                            media_info["name"] = upload_result["file_name"]
                            media_info["size_bytes"] = upload_result["file_size"]
                            media_info["mime_type"] = upload_result["mime_type"]
                        else:
                            logger.warning(f"下载会话存档媒体失败: sdkfileid={sdkfileid}")

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

            # 6.1 渠道入站消息：触发客户画像洞察飞轮（失败不影响主流程）
            try:
                if channel_message.message_type == "text" and direction == "inbound":
                    txt = str((channel_message.content or {}).get("text") or "").strip()
                    if txt:
                        enqueue_customer_insight_job(
                            customer_id=customer_user_id,
                            conversation_id=str(conversation.id),
                            message_id=str(message_info.id),
                        )
            except Exception as e:
                logger.warning(
                    f"触发渠道客户画像洞察任务失败（已忽略）: conversation_id={conversation.id}, err={e}",
                    exc_info=True,
                )
            
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
    
    async def _get_or_create_conversation(
        self,
        *,
        channel_message: ChannelMessage,
        owner_user_id: str,
        owner_display_name: Optional[str],
    ) -> Conversation:
        """
        获取或创建会话

        会话唯一性：tag=channel + extra_metadata.channel.type + extra_metadata.channel.peer_id
        """
        from sqlalchemy import cast, String
        from app.common.deps.uuid_utils import conversation_id

        peer_id = channel_message.channel_user_id
        channel_type = channel_message.channel_type

        logger.info(f"查找或创建渠道会话: channel_type={channel_type}, peer_id={peer_id}")

        existing = None

        # 方法1：SQL 查询（性能好）
        try:
            existing = (
                self.db.query(Conversation)
                .filter(
                    Conversation.tag == "channel",
                    Conversation.extra_metadata.isnot(None),
                    cast(Conversation.extra_metadata["channel"]["type"], String) == channel_type,
                    cast(Conversation.extra_metadata["channel"]["peer_id"], String) == peer_id,
                )
                .first()
            )
        except Exception as e:
            logger.warning(f"SQL查询渠道会话失败，将使用Python方式查询: {e}")

        # 方法2：Python 兜底（更鲁棒）
        if not existing:
            try:
                all_channel_convs = (
                    self.db.query(Conversation)
                    .filter(Conversation.tag == "channel", Conversation.extra_metadata.isnot(None))
                    .all()
                )

                for conv in all_channel_convs:
                    if not isinstance(conv.extra_metadata, dict):
                        continue
                    channel_meta = conv.extra_metadata.get("channel")
                    if not isinstance(channel_meta, dict):
                        continue
                    if channel_meta.get("type") == channel_type and str(channel_meta.get("peer_id")) == str(peer_id):
                        existing = conv
                        logger.info(
                            f"通过Python方式找到已存在的渠道会话: conversation_id={conv.id}, channel_type={channel_type}, peer_id={peer_id}"
                        )
                        break
            except Exception as e:
                logger.error(f"Python方式查询渠道会话也失败: {e}", exc_info=True)

        peer_name = channel_message.extra_data.get("peer_name") if channel_message.extra_data else None

        if existing:
            # 修正历史占位 owner（以及同步 channel meta）
            need_update = False
            if str(existing.owner_id) != str(owner_user_id):
                existing.owner_id = str(owner_user_id)
                need_update = True

            if not isinstance(existing.extra_metadata, dict):
                existing.extra_metadata = {}
                need_update = True

            ch = existing.extra_metadata.get("channel")
            if not isinstance(ch, dict):
                ch = {}
                existing.extra_metadata["channel"] = ch
                need_update = True

            if ch.get("customer_user_id") != str(owner_user_id):
                ch["customer_user_id"] = str(owner_user_id)
                need_update = True
            if peer_name and ch.get("peer_name") != peer_name:
                ch["peer_name"] = peer_name
                need_update = True

            if need_update:
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(existing, "extra_metadata")
                self.db.commit()
                self.db.refresh(existing)

            logger.info(f"找到已存在的渠道会话: conversation_id={existing.id}, channel_type={channel_type}, peer_id={peer_id}")
            return existing

        logger.info(f"未找到匹配的渠道会话，将创建新会话: channel_type={channel_type}, peer_id={peer_id}")

        title = owner_display_name or (peer_name.strip() if isinstance(peer_name, str) and peer_name.strip() else None) or f"{channel_type}:{peer_id}"

        logger.info(f"创建新的渠道会话: title={title}, channel_type={channel_type}, peer_id={peer_id}")

        conversation = Conversation(
            id=conversation_id(),
            title=title,
            owner_id=str(owner_user_id),
            chat_mode="single",
            tag="channel",
            extra_metadata={
                "channel": {
                    "type": channel_type,
                    "peer_id": peer_id,
                    "peer_name": peer_name,
                    "customer_user_id": str(owner_user_id),
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

    def _resolve_or_create_customer_user(self, channel_message: ChannelMessage) -> tuple[str, Optional[str]]:
        """
        将外部渠道 peer_id 归一为系统内 customer(User)。

        返回：
        - customer_user_id: str
        - display_name: Optional[str]
        """
        from app.identity_access.enums import UserStatus
        from app.identity_access.models.user import User, Role
        from app.common.deps.uuid_utils import role_id
        from app.core.password_utils import get_password_hash

        channel_type = channel_message.channel_type
        peer_id = str(channel_message.channel_user_id)
        peer_name = None
        if channel_message.extra_data and isinstance(channel_message.extra_data, dict):
            peer_name = channel_message.extra_data.get("peer_name")
            # 可选：上游已完成匹配时，可直接指定绑定到某个 customer_user_id
            prebind_customer_user_id = channel_message.extra_data.get("customer_user_id") or channel_message.extra_data.get("bind_to_customer_user_id")
            if isinstance(prebind_customer_user_id, str) and prebind_customer_user_id.strip():
                prebind_customer_user_id = prebind_customer_user_id.strip()
                user = self.db.query(User).filter(User.id == prebind_customer_user_id).first()
                if user:
                    # upsert identity 到指定 customer，并直接返回
                    identity = (
                        self.db.query(ChannelIdentity)
                        .filter(ChannelIdentity.channel_type == channel_type, ChannelIdentity.peer_id == peer_id)
                        .first()
                    )
                    if identity:
                        identity.user_id = str(user.id)
                        if peer_name:
                            identity.peer_name = peer_name
                        if channel_message.extra_data:
                            identity.extra_data = channel_message.extra_data
                    else:
                        identity = ChannelIdentity(
                            channel_type=channel_type,
                            peer_id=peer_id,
                            user_id=str(user.id),
                            peer_name=peer_name,
                            extra_data=channel_message.extra_data,
                        )
                        self.db.add(identity)
                    from sqlalchemy.sql import func
                    identity.last_seen_at = func.now()
                    self.db.commit()
                    self.db.refresh(identity)
                    return str(user.id), peer_name

        existing = (
            self.db.query(ChannelIdentity)
            .filter(
                ChannelIdentity.channel_type == channel_type,
                ChannelIdentity.peer_id == peer_id,
            )
            .first()
        )
        if existing:
            # 更新展示名与 last_seen_at
            if peer_name and peer_name != existing.peer_name:
                existing.peer_name = peer_name
            existing.extra_data = channel_message.extra_data if channel_message.extra_data else existing.extra_data
            # last_seen_at 交由数据库更新时间戳也可以，这里显式更新更直观
            from sqlalchemy.sql import func
            existing.last_seen_at = func.now()
            self.db.commit()
            self.db.refresh(existing)
            return str(existing.user_id), existing.peer_name

        # 新客：创建 User(customer) + Customer/CustomerProfile + ChannelIdentity
        peer_hash = hashlib.sha1(peer_id.encode("utf-8")).hexdigest()[:10]
        safe_channel = "".join([c if c.isalnum() or c in ("_", "-") else "_" for c in channel_type])[:20]
        username = (str(peer_name).strip() if isinstance(peer_name, str) and peer_name.strip() else None) or f"客户_{safe_channel}_{peer_hash[:6]}"
        email = f"ch_{safe_channel}_{peer_hash}@channel.local"

        # 保障 username/email 的唯一性（极小概率碰撞时追加随机后缀）
        if self.db.query(User).filter(User.email == email).first():
            email = f"ch_{safe_channel}_{peer_hash}_{secrets.token_hex(2)}@channel.local"
        if self.db.query(User).filter(User.username == username).first():
            username = f"{username}_{secrets.token_hex(2)}"

        pwd = secrets.token_urlsafe(24)
        user = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(pwd),
            status=UserStatus.ACTIVE,
        )

        role = self.db.query(Role).filter(Role.name == "customer").first()
        if not role:
            role = Role(id=role_id(), name="customer")
            self.db.add(role)
            self.db.flush()
        user.roles.append(role)

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # 创建 Customer 记录 + Profile（复用 CustomerService 的最小创建逻辑）
        try:
            from app.customer.services.customer_service import CustomerService
            CustomerService(self.db).create_customer(user_id=str(user.id))
        except Exception as e:
            logger.warning(f"创建 Customer/Profile 失败（将继续，稍后可补齐）: user_id={user.id}, err={e}", exc_info=True)

        identity = ChannelIdentity(
            channel_type=channel_type,
            peer_id=peer_id,
            user_id=str(user.id),
            peer_name=peer_name,
            extra_data=channel_message.extra_data,
        )
        self.db.add(identity)
        self.db.commit()
        self.db.refresh(identity)

        return str(user.id), peer_name
