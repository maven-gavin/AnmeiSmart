import logging
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

from app.channels.models.channel_config import ChannelConfig

logger = logging.getLogger(__name__)


class WeChatWorkContactService:
    TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    CONTACT_URL = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/get"

    def __init__(self, db: Session):
        self.db = db

    def _load_config(self) -> Optional[dict[str, Any]]:
        config = (
            self.db.query(ChannelConfig)
            .filter(
                ChannelConfig.channel_type == "wechat_work_contact",
                ChannelConfig.is_active.is_(True),
            )
            .order_by(ChannelConfig.created_at.desc())
            .first()
        )
        if config and isinstance(config.config, dict):
            return config.config
        return None

    async def _get_access_token(self, corp_id: str, secret: str) -> str:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(self.TOKEN_URL, params={"corpid": corp_id, "corpsecret": secret})
            resp.raise_for_status()
            data = resp.json()
            if data.get("errcode") != 0:
                raise RuntimeError(f"获取 access_token 失败: {data.get('errmsg')} ({data.get('errcode')})")
            return data["access_token"]

    async def get_external_contact(self, *, external_userid: str) -> Optional[dict[str, Any]]:
        cfg = self._load_config()
        if not cfg:
            return None

        corp_id = str(cfg.get("corp_id") or "")
        secret = str(cfg.get("secret") or "")
        if not corp_id or not secret:
            return None

        access_token = await self._get_access_token(corp_id, secret)
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                self.CONTACT_URL,
                params={"access_token": access_token, "external_userid": external_userid},
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("errcode") != 0:
                logger.warning(f"获取外部联系人失败: {data.get('errmsg')} ({data.get('errcode')})")
                return None
            external = data.get("external_contact") or {}
            follow_user = data.get("follow_user") or []
            mobile = None
            if isinstance(follow_user, list) and follow_user:
                first = follow_user[0]
                if isinstance(first, dict):
                    mobile = first.get("remark_mobiles")
                    if isinstance(mobile, list) and mobile:
                        mobile = mobile[0]
            return {
                "name": external.get("name"),
                "unionid": external.get("unionid"),
                "mobile": mobile,
                "raw": data,
            }
import json
import logging
from typing import Any, Optional

import httpx
from sqlalchemy.orm import Session

from app.channels.models.channel_config import ChannelConfig
from app.core.redis_client import redis_manager

logger = logging.getLogger(__name__)


class WeChatWorkContactService:
    """企业微信客户联系信息服务（外部联系人详情）"""

    TOKEN_URL = "https://qyapi.weixin.qq.com/cgi-bin/gettoken"
    CONTACT_GET_URL = "https://qyapi.weixin.qq.com/cgi-bin/externalcontact/get"

    def __init__(self, db: Session):
        self.db = db

    def _load_config(self) -> Optional[dict[str, Any]]:
        row = (
            self.db.query(ChannelConfig)
            .filter(ChannelConfig.channel_type == "wechat_work_contact", ChannelConfig.is_active.is_(True))
            .order_by(ChannelConfig.created_at.desc())
            .first()
        )
        if row and isinstance(row.config, dict):
            return row.config
        return None

    async def _get_access_token(self, corp_id: str, secret: str) -> str:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(self.TOKEN_URL, params={"corpid": corp_id, "corpsecret": secret})
            resp.raise_for_status()
            data = resp.json()
            if data.get("errcode") != 0:
                raise RuntimeError(f"获取客户联系 access_token 失败: {data.get('errmsg')} ({data.get('errcode')})")
            return data["access_token"]

    async def get_external_contact(self, *, external_userid: str) -> Optional[dict[str, Any]]:
        cfg = self._load_config()
        if not cfg:
            return None

        corp_id = str(cfg.get("corp_id") or "")
        secret = str(cfg.get("secret") or "")
        if not corp_id or not secret:
            return None

        cache_key = f"wechat_work_contact:{external_userid}"
        try:
            client = await redis_manager.get_client()
            cached = await client.get(cache_key)
            if cached:
                return json.loads(cached)
        except Exception:
            pass

        try:
            token = await self._get_access_token(corp_id, secret)
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    self.CONTACT_GET_URL,
                    params={"access_token": token, "external_userid": external_userid},
                )
                resp.raise_for_status()
                data = resp.json()
                if data.get("errcode") != 0:
                    logger.warning(f"获取外部联系人失败: {data.get('errmsg')} ({data.get('errcode')})")
                    return None
                profile = data.get("external_contact") or {}
                follow_user = data.get("follow_user") or []
                result = {
                    "external_userid": external_userid,
                    "name": profile.get("name"),
                    "unionid": profile.get("unionid"),
                    "mobile": profile.get("mobile"),
                    "corp_name": profile.get("corp_name"),
                    "company_name": profile.get("corp_full_name"),
                    "type": profile.get("type"),
                    "gender": profile.get("gender"),
                    "avatar": profile.get("avatar"),
                    "follow_user": follow_user,
                }

                try:
                    cache_client = await redis_manager.get_client()
                    await cache_client.set(cache_key, json.dumps(result), ex=3600)
                except Exception:
                    pass

                return result
        except Exception as e:
            logger.warning(f"获取外部联系人异常: {e}", exc_info=True)
            return None
