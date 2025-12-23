"""
企业微信 - 微信客服 渠道适配器
"""
from __future__ import annotations

import json
import logging
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional

from fastapi import Request

from app.channels.interfaces import ChannelAdapter, ChannelMessage
from app.chat.models.chat import Message
from app.channels.adapters.wechat_work.crypto import WeChatWorkCrypto
from app.channels.adapters.wechat_work.kf_client import WeChatWorkKfClient

logger = logging.getLogger(__name__)


class WeChatWorkKfAdapter(ChannelAdapter):
    """微信客服渠道适配器（外部联系人/客户）"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.corp_id: str = config["corp_id"]
        self.secret: str = config["secret"]
        self.open_kfid: Optional[str] = config.get("open_kfid")
        self.token: str = config.get("token", "")
        self.encoding_aes_key: str = config.get("encoding_aes_key", "")

        self.client = WeChatWorkKfClient(corp_id=self.corp_id, secret=self.secret)
        self.crypto: Optional[WeChatWorkCrypto] = None
        if self.token and self.encoding_aes_key and self.corp_id:
            self.crypto = WeChatWorkCrypto(token=self.token, encoding_aes_key=self.encoding_aes_key, corp_id=self.corp_id)

    def get_channel_type(self) -> str:
        return "wechat_work_kf"

    async def validate_webhook(self, request: Request) -> bool:
        """验证回调签名（GET 使用 echostr，POST 使用 Encrypt）"""
        query = request.query_params
        msg_signature = query.get("msg_signature")
        timestamp = query.get("timestamp")
        nonce = query.get("nonce")

        if not all([msg_signature, timestamp, nonce]):
            return False

        if not self.crypto:
            # 没配置 token/encodingAESKey 的情况下，无法做强校验
            return True

        # GET 校验：使用 echostr
        echostr = query.get("echostr")
        if echostr:
            return self.crypto.verify_signature(msg_signature=msg_signature, timestamp=timestamp, nonce=nonce, value=echostr)

        # POST 校验：优先从 body 的 Encrypt 字段校验（由 controller 解密时传入也行）
        # 这里不读 body（避免重复读取流），controller 会在解密前做校验
        return True

    def decrypt_echostr(self, encrypted_echostr: str) -> Optional[str]:
        if not self.crypto:
            return None
        return self.crypto.decrypt_echostr(encrypted_echostr)

    def decrypt_encrypt_field(self, encrypt_b64: str) -> Optional[str]:
        if not self.crypto:
            return None
        return self.crypto.decrypt_encrypt_field(encrypt_b64)

    @staticmethod
    def _parse_xml(xml_content: str) -> Dict[str, Any]:
        root = ET.fromstring(xml_content)
        result: Dict[str, Any] = {}
        for child in root:
            result[child.tag] = child.text
        return result

    @staticmethod
    def _extract_encrypt_from_xml(xml_content: str) -> Optional[str]:
        try:
            data = WeChatWorkKfAdapter._parse_xml(xml_content)
            return data.get("Encrypt")
        except Exception:
            return None

    def parse_incoming_payload(self, raw_body: str) -> Dict[str, Any]:
        """
        微信客服回调的明文可能是 XML 或 JSON（不同场景/版本会有差异）
        这里做一个宽松解析：
        - 以 '<' 开头 -> XML
        - 以 '{' 开头 -> JSON
        """
        s = (raw_body or "").strip()
        if not s:
            return {}
        if s.startswith("<"):
            return self._parse_xml(s)
        if s.startswith("{"):
            return json.loads(s)
        # 默认尝试 JSON
        return json.loads(s)

    async def receive_message(self, raw_message: Dict[str, Any]) -> ChannelMessage:
        """
        将微信客服消息转换为统一 ChannelMessage
        关键字段（常见）：
        - MsgId / msgid
        - ExternalUserId / external_userid（客户标识）
        - MsgType / msgtype
        - Content / text.content
        - OpenKfId / open_kfid
        """
        msg_type = raw_message.get("MsgType") or raw_message.get("msgtype") or ""
        msg_id = raw_message.get("MsgId") or raw_message.get("msgid") or ""
        external_userid = raw_message.get("ExternalUserId") or raw_message.get("external_userid") or ""
        open_kfid = raw_message.get("OpenKfId") or raw_message.get("open_kfid") or raw_message.get("OpenKfID") or ""

        if not external_userid:
            # 某些事件型回调可能没有 external_userid（如状态变更），先忽略
            raise ValueError("微信客服回调缺少 external_userid")

        if msg_type == "text":
            content = raw_message.get("Content")
            if not content and isinstance(raw_message.get("text"), dict):
                content = raw_message["text"].get("content")
            return ChannelMessage(
                channel_type=self.get_channel_type(),
                channel_message_id=str(msg_id) if msg_id else f"{open_kfid}:{external_userid}",
                channel_user_id=str(external_userid),
                content={"text": content or ""},
                message_type="text",
                timestamp=raw_message.get("CreateTime") or raw_message.get("create_time") or 0,
                extra_data={
                    "open_kfid": open_kfid,
                },
            )

        logger.warning(f"暂不支持的微信客服消息类型: {msg_type}")
        raise ValueError(f"不支持的微信客服消息类型: {msg_type}")

    async def send_message(self, message: Message, channel_user_id: str) -> bool:
        """通过微信客服发送消息给外部联系人"""
        if not self.open_kfid:
            logger.error("未配置 open_kfid，无法通过微信客服发送外部消息（请设置 WECHAT_WORK_KF_OPEN_KFID）")
            return False

        if message.type != "text":
            logger.warning("微信客服当前仅实现文本消息发送")
            return False

        content = (message.content or {}).get("text", "")
        extra = message.extra_metadata or {}
        channel_meta = extra.get("channel") if isinstance(extra, dict) else None
        from_user_name = channel_meta.get("from_user_name") if isinstance(channel_meta, dict) else None
        if from_user_name:
            content = f"【{from_user_name}】{content}"

        return await self.client.send_text(open_kfid=self.open_kfid, external_userid=channel_user_id, content=content)


