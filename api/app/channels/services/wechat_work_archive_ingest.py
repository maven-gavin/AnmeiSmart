import logging
import mimetypes
from typing import Any, Iterable

from app.channels.interfaces import ChannelMessage
from app.channels.services.channel_service import ChannelService
from app.channels.services.wechat_work_archive_utils import extract_external_user_id
from app.channels.services.wechat_work_contact_service import WeChatWorkContactService
from app.channels.services.channel_identity_service import ChannelIdentityService

logger = logging.getLogger(__name__)


async def ingest_decrypted_messages(
    messages: Iterable[dict[str, Any]],
    *,
    channel_service: ChannelService,
    enable_contact_enrichment: bool = True,
) -> int:
    processed = 0
    profile_cache: dict[str, dict[str, Any]] = {}
    contact_service = WeChatWorkContactService(db=channel_service.db)
    identity_service = ChannelIdentityService(db=channel_service.db)

    for msg in messages:
        if not isinstance(msg, dict):
            continue

        external_userid = extract_external_user_id(msg) or ""
        if not external_userid:
            continue

        msgtype = str(msg.get("msgtype") or "").lower()
        if msgtype not in {"text", "image", "file"}:
            continue

        direction = "inbound" if msg.get("from") == external_userid else "outbound"
        extra_data = {
            "direction": direction,
            "from_user_id": msg.get("from"),
            "to_user_ids": msg.get("tolist"),
            "room_id": msg.get("roomid"),
            "peer_name": msg.get("extname") or msg.get("external_name"),
        }

        if enable_contact_enrichment:
            profile = profile_cache.get(external_userid)
            if profile is None:
                profile = await contact_service.get_external_contact(external_userid=external_userid) or {}
                profile_cache[external_userid] = profile

            if profile:
                extra_data["contact_profile"] = profile
                if profile.get("name"):
                    extra_data["peer_name"] = profile.get("name")
                if profile.get("unionid"):
                    extra_data["unionid"] = profile.get("unionid")
                if profile.get("mobile"):
                    extra_data["mobile"] = profile.get("mobile")
                bind_user_id = identity_service.resolve_customer_by_profile(
                    unionid=profile.get("unionid"),
                    phone=profile.get("mobile"),
                )
                if bind_user_id:
                    extra_data["bind_to_customer_user_id"] = bind_user_id

        if msgtype == "text":
            text_obj = msg.get("text") or {}
            content = str(text_obj.get("content") or "").strip()
            if not content:
                continue

            channel_message = ChannelMessage(
                channel_type="wechat_work_contact",
                channel_message_id=str(msg.get("msgid") or ""),
                channel_user_id=external_userid,
                content={"text": content},
                message_type="text",
                timestamp=int(msg.get("msgtime") or 0),
                extra_data=extra_data,
            )
        else:
            media_info: dict[str, Any] = {}
            if msgtype == "image":
                image = msg.get("image") or {}
                media_info = {
                    "sdkfileid": image.get("sdkfileid"),
                    "name": "image.jpg",
                    "size_bytes": image.get("filesize") or 0,
                    "mime_type": "image/jpeg",
                }
            else:
                file_obj = msg.get("file") or {}
                filename = file_obj.get("filename") or "file.bin"
                mime_type, _ = mimetypes.guess_type(filename)
                media_info = {
                    "sdkfileid": file_obj.get("sdkfileid"),
                    "name": filename,
                    "size_bytes": file_obj.get("filesize") or 0,
                    "mime_type": mime_type or "application/octet-stream",
                }

            if not media_info.get("sdkfileid"):
                continue

            channel_message = ChannelMessage(
                channel_type="wechat_work_contact",
                channel_message_id=str(msg.get("msgid") or ""),
                channel_user_id=external_userid,
                content={"media_info": media_info},
                message_type="media",
                timestamp=int(msg.get("msgtime") or 0),
                extra_data=extra_data,
            )

        try:
            await channel_service.process_incoming_message(channel_message)
            processed += 1
        except Exception as e:
            logger.warning(f"处理会话存档消息失败: {e}", exc_info=True)

    return processed
