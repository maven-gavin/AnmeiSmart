"""
企业微信会话内容存档 - 拉取与解密服务
"""
from __future__ import annotations

import base64
import json
import logging
import os
from typing import Any, Optional, Tuple, List

import httpx
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives import padding as sym_padding
from sqlalchemy.orm import Session

from app.channels.models.channel_config import ChannelConfig
from app.core.redis_client import redis_manager

logger = logging.getLogger(__name__)


class WeChatWorkArchiveService:
    """
    企业微信会话内容存档服务
    负责拉取加密数据并解密为可用 chatdata
    """

    TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    ARCHIVE_URL = "https://qyapi.weixin.qq.com/cgi-bin/msgaudit/getchatdata"

    def __init__(self, db: Session):
        self.db = db

    def _load_config(self) -> Optional[dict[str, Any]]:
        config = (
            self.db.query(ChannelConfig)
            .filter(
                ChannelConfig.channel_type == "wechat_work_archive",
                ChannelConfig.is_active.is_(True),
            )
            .order_by(ChannelConfig.created_at.desc())
            .first()
        )
        if config and isinstance(config.config, dict):
            return config.config

        # 临时兼容：允许使用环境变量（后续可迁移到后台配置）
        corp_id = os.getenv("WECHAT_WORK_CORP_ID")
        secret = os.getenv("WECHAT_WORK_ARCHIVE_SECRET")
        private_key = os.getenv("WECHAT_WORK_ARCHIVE_PRIVATE_KEY")
        private_key_path = os.getenv("WECHAT_WORK_ARCHIVE_PRIVATE_KEY_PATH")

        if corp_id and secret and (private_key or private_key_path):
            logger.warning("会话内容存档配置来自环境变量（建议迁移到 ChannelConfig）")
            return {
                "corp_id": corp_id,
                "secret": secret,
                "private_key": private_key,
                "private_key_path": private_key_path,
                "last_seq": 0,
            }
        return None

    def _load_private_key(self, cfg: dict[str, Any]) -> bytes:
        if cfg.get("private_key"):
            return str(cfg["private_key"]).encode("utf-8")
        if cfg.get("private_key_path"):
            with open(cfg["private_key_path"], "rb") as f:
                return f.read()
        raise ValueError("未配置会话内容存档私钥")

    async def _get_access_token(self, corp_id: str, secret: str) -> str:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(self.TOKEN_URL, params={"corpid": corp_id, "corpsecret": secret})
            resp.raise_for_status()
            data = resp.json()
            if data.get("errcode") != 0:
                raise RuntimeError(f"获取 access_token 失败: {data.get('errmsg')} ({data.get('errcode')})")
            return data["access_token"]

    async def _get_last_seq(self, cfg: dict[str, Any]) -> int:
        # 优先尝试 Redis
        try:
            client = await redis_manager.get_client()
            val = await client.get("wechat_work_archive:last_seq")
            if val is not None:
                return int(val)
        except Exception:
            pass

        # 其次使用 ChannelConfig
        val = cfg.get("last_seq")
        try:
            return int(val) if val is not None else 0
        except Exception:
            return 0

    async def _set_last_seq(self, cfg: dict[str, Any], seq: int) -> None:
        # 写入 Redis
        try:
            client = await redis_manager.get_client()
            await client.set("wechat_work_archive:last_seq", str(seq))
        except Exception:
            pass

        # 写回 ChannelConfig（如果存在）
        config_row = (
            self.db.query(ChannelConfig)
            .filter(
                ChannelConfig.channel_type == "wechat_work_archive",
                ChannelConfig.is_active.is_(True),
            )
            .order_by(ChannelConfig.created_at.desc())
            .first()
        )
        if config_row and isinstance(config_row.config, dict):
            config_row.config = {**config_row.config, "last_seq": seq}
            self.db.add(config_row)
            self.db.commit()

    def _decrypt_random_key(self, private_key_pem: bytes, encrypted_random_key_b64: str) -> bytes:
        private_key = load_pem_private_key(private_key_pem, password=None)
        encrypted = base64.b64decode(encrypted_random_key_b64)
        return private_key.decrypt(
            encrypted,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA1()), algorithm=hashes.SHA1(), label=None),
        )

    def _decrypt_chat_msg(self, random_key: bytes, encrypted_chat_msg_b64: str) -> Optional[dict[str, Any]]:
        raw = base64.b64decode(encrypted_chat_msg_b64)

        # 方案A：前16字节为IV
        for iv, ciphertext in ((raw[:16], raw[16:]), (random_key[:16], raw)):
            try:
                cipher = Cipher(algorithms.AES(random_key), modes.CBC(iv))
                decryptor = cipher.decryptor()
                padded = decryptor.update(ciphertext) + decryptor.finalize()

                unpadder = sym_padding.PKCS7(128).unpadder()
                data = unpadder.update(padded) + unpadder.finalize()
                text = data.decode("utf-8")
                return json.loads(text)
            except Exception:
                continue

        return None

    async def pull_chatdata(self, *, seq: Optional[int] = None, limit: int = 100) -> Tuple[List[dict[str, Any]], int]:
        cfg = self._load_config()
        if not cfg:
            raise RuntimeError("会话内容存档配置缺失")

        corp_id = str(cfg.get("corp_id") or "")
        secret = str(cfg.get("secret") or "")
        if not corp_id or not secret:
            raise RuntimeError("会话内容存档配置缺少 corp_id 或 secret")

        private_key_pem = self._load_private_key(cfg)
        access_token = await self._get_access_token(corp_id, secret)
        last_seq = seq if seq is not None else await self._get_last_seq(cfg)

        payload = {"seq": last_seq, "limit": limit}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(self.ARCHIVE_URL, params={"access_token": access_token}, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if data.get("errcode") != 0:
                raise RuntimeError(f"拉取会话存档失败: {data.get('errmsg')} ({data.get('errcode')})")

        decrypted: list[dict[str, Any]] = []
        max_seq = last_seq
        for item in data.get("chatdata") or []:
            if not isinstance(item, dict):
                continue
            item_seq = item.get("seq")
            try:
                if isinstance(item_seq, int) and item_seq > max_seq:
                    max_seq = item_seq
            except Exception:
                pass

            enc_key = item.get("encrypt_random_key")
            enc_msg = item.get("encrypt_chat_msg")
            if not enc_key or not enc_msg:
                continue

            try:
                random_key = self._decrypt_random_key(private_key_pem, enc_key)
                msg = self._decrypt_chat_msg(random_key, enc_msg)
                if msg:
                    decrypted.append(msg)
            except Exception as e:
                logger.warning(f"解密会话存档消息失败: {e}")

        next_seq = max_seq + 1 if max_seq >= last_seq else last_seq
        await self._set_last_seq(cfg, next_seq)
        return decrypted, next_seq

