"""
ChannelIdentityService

用于支持：
- 把 channel_type + peer_id 绑定到已有 customer(User)，避免重复建客户
- 迁移/修正历史映射，并同步修正 tag=channel 会话的 owner_id
"""

import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.channels.models.channel_identity import ChannelIdentity
from app.chat.models.chat import Conversation
from app.core.api import BusinessException, ErrorCode
from app.identity_access.models.user import User

logger = logging.getLogger(__name__)


class ChannelIdentityService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_type_peer(self, *, channel_type: str, peer_id: str) -> Optional[ChannelIdentity]:
        return (
            self.db.query(ChannelIdentity)
            .filter(
                ChannelIdentity.channel_type == channel_type,
                ChannelIdentity.peer_id == peer_id,
            )
            .first()
        )

    def list_by_customer(self, *, customer_user_id: str) -> list[ChannelIdentity]:
        return (
            self.db.query(ChannelIdentity)
            .filter(ChannelIdentity.user_id == customer_user_id)
            .order_by(ChannelIdentity.last_seen_at.desc())
            .all()
        )

    def bind_identity(
        self,
        *,
        channel_type: str,
        peer_id: str,
        customer_user_id: str,
        peer_name: Optional[str] = None,
        extra_data: Optional[dict[str, Any]] = None,
        migrate_conversations: bool = True,
    ) -> ChannelIdentity:
        """
        将一个渠道身份绑定到指定 customer(User)。

        - 如果该 identity 已存在：更新 user_id（迁移）与 peer_name/extra_data
        - 如果不存在：创建一条新映射（实现“先绑定再入站”的流程）
        - 可选：同步修正 tag=channel 的历史会话 owner_id 与 channel 元数据
        """
        user = self.db.query(User).filter(User.id == customer_user_id).first()
        if not user:
            raise BusinessException("目标客户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)

        identity = self.get_by_type_peer(channel_type=channel_type, peer_id=peer_id)

        if identity:
            identity.user_id = customer_user_id
            if peer_name:
                identity.peer_name = peer_name
            if extra_data is not None:
                identity.extra_data = extra_data
        else:
            identity = ChannelIdentity(
                channel_type=channel_type,
                peer_id=peer_id,
                user_id=customer_user_id,
                peer_name=peer_name,
                extra_data=extra_data,
            )
            self.db.add(identity)

        # last_seen_at 使用数据库函数更新时间（避免依赖本地时钟）
        from sqlalchemy.sql import func

        identity.last_seen_at = func.now()

        self.db.commit()
        self.db.refresh(identity)

        if migrate_conversations:
            self._migrate_channel_conversations(
                channel_type=channel_type,
                peer_id=peer_id,
                customer_user_id=customer_user_id,
                peer_name=peer_name,
            )

        return identity

    def _migrate_channel_conversations(
        self,
        *,
        channel_type: str,
        peer_id: str,
        customer_user_id: str,
        peer_name: Optional[str],
    ) -> int:
        """
        将历史 tag=channel 会话的 owner_id 纠正为目标 customer，并同步写入 extra_metadata.channel.customer_user_id。
        返回迁移的会话数量。
        """
        from sqlalchemy import cast, String

        updated = 0
        convs: list[Conversation] = []

        # SQL 优先（快）
        try:
            convs = (
                self.db.query(Conversation)
                .filter(
                    Conversation.tag == "channel",
                    Conversation.extra_metadata.isnot(None),
                    cast(Conversation.extra_metadata["channel"]["type"], String) == channel_type,
                    cast(Conversation.extra_metadata["channel"]["peer_id"], String) == str(peer_id),
                )
                .all()
            )
        except Exception as e:
            logger.warning(f"迁移渠道会话：SQL 查询失败，将使用 Python 兜底: {e}")

        # Python 兜底（鲁棒，但慢）
        if not convs:
            all_channel_convs = (
                self.db.query(Conversation)
                .filter(Conversation.tag == "channel", Conversation.extra_metadata.isnot(None))
                .all()
            )
            for c in all_channel_convs:
                if not isinstance(c.extra_metadata, dict):
                    continue
                ch = c.extra_metadata.get("channel")
                if not isinstance(ch, dict):
                    continue
                if ch.get("type") == channel_type and str(ch.get("peer_id")) == str(peer_id):
                    convs.append(c)

        if not convs:
            return 0

        for conv in convs:
            need_update = False
            if str(conv.owner_id) != str(customer_user_id):
                conv.owner_id = str(customer_user_id)
                need_update = True

            if not isinstance(conv.extra_metadata, dict):
                conv.extra_metadata = {}
                need_update = True

            ch = conv.extra_metadata.get("channel")
            if not isinstance(ch, dict):
                ch = {}
                conv.extra_metadata["channel"] = ch
                need_update = True

            if ch.get("customer_user_id") != str(customer_user_id):
                ch["customer_user_id"] = str(customer_user_id)
                need_update = True

            if peer_name and ch.get("peer_name") != peer_name:
                ch["peer_name"] = peer_name
                need_update = True

            if need_update:
                # JSON 的嵌套字段原地修改默认不会被 SQLAlchemy 追踪，这里显式标记为已修改
                from sqlalchemy.orm.attributes import flag_modified
                flag_modified(conv, "extra_metadata")
                updated += 1

        if updated:
            self.db.commit()

        return updated

    def merge_customer_identities(
        self,
        *,
        source_customer_user_id: str,
        target_customer_user_id: str,
        migrate_conversations: bool = True,
    ) -> int:
        """
        将 source_customer_user_id 的所有 ChannelIdentity 合并到 target_customer_user_id。

        返回迁移的 identity 数量。
        """
        if source_customer_user_id == target_customer_user_id:
            return 0

        target = self.db.query(User).filter(User.id == target_customer_user_id).first()
        if not target:
            raise BusinessException("目标客户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)

        identities = self.list_by_customer(customer_user_id=source_customer_user_id)
        if not identities:
            return 0

        moved = 0
        for identity in identities:
            identity.user_id = target_customer_user_id
            moved += 1

        self.db.commit()

        if migrate_conversations:
            # 同步修正相关会话 owner（按 identity 逐个迁移即可）
            for identity in identities:
                self._migrate_channel_conversations(
                    channel_type=identity.channel_type,
                    peer_id=identity.peer_id,
                    customer_user_id=target_customer_user_id,
                    peer_name=identity.peer_name,
                )

        return moved

