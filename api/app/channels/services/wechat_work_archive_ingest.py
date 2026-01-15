import logging
from typing import Any, Iterable

from app.channels.interfaces import ChannelMessage
from app.channels.services.channel_service import ChannelService
from app.channels.services.wechat_work_archive_utils import extract_external_user_id

logger = logging.getLogger(__name__)


async def ingest_decrypted_messages(
    messages: Iterable[dict[str, Any]],
    *,
    channel_service: ChannelService,
) -> int:
    processed = 0
    for msg in messages:
        if not isinstance(msg, dict):
            continue

        external_userid = extract_external_user_id(msg) or ""
        if not external_userid:
            continue

        msgtype = str(msg.get("msgtype") or "").lower()
        if msgtype != "text":
            continue

        text_obj = msg.get("text") or {}
        content = str(text_obj.get("content") or "").strip()
        if not content:
            continue

        direction = "inbound" if msg.get("from") == external_userid else "outbound"
        channel_message = ChannelMessage(
            channel_type="wechat_work_contact",
            channel_message_id=str(msg.get("msgid") or ""),
            channel_user_id=external_userid,
            content={"text": content},
            message_type="text",
            timestamp=int(msg.get("msgtime") or 0),
            extra_data={
                "direction": direction,
                "from_user_id": msg.get("from"),
                "to_user_ids": msg.get("tolist"),
                "room_id": msg.get("roomid"),
                "peer_name": msg.get("extname") or msg.get("external_name"),
            },
        )
        try:
            await channel_service.process_incoming_message(channel_message)
            processed += 1
        except Exception as e:
            logger.warning(f"处理会话存档消息失败: {e}", exc_info=True)
    return processed
