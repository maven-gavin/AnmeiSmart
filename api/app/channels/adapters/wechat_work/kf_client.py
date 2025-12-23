"""
企业微信 - 微信客服 API 客户端
"""
from __future__ import annotations

import logging
from typing import Optional, Any

import httpx

logger = logging.getLogger(__name__)


class WeChatWorkKfClient:
    """微信客服 API 客户端（需要 corpsecret=客服secret）"""

    BASE_URL = "https://qyapi.weixin.qq.com"

    def __init__(self, corp_id: str, secret: str):
        self.corp_id = corp_id
        self.secret = secret

    async def get_access_token(self) -> str:
        url = f"{self.BASE_URL}/cgi-bin/gettoken"
        params = {"corpid": self.corp_id, "corpsecret": self.secret}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            if data.get("errcode") != 0:
                raise RuntimeError(f"获取access_token失败: {data.get('errmsg')} ({data.get('errcode')})")
            return data["access_token"]

    async def list_accounts(self) -> list[dict[str, Any]]:
        token = await self.get_access_token()
        url = f"{self.BASE_URL}/cgi-bin/kf/account/list"
        params = {"access_token": token}
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, params=params, json={})
            resp.raise_for_status()
            data = resp.json()
            if data.get("errcode") != 0:
                raise RuntimeError(f"获取客服账号列表失败: {data.get('errmsg')} ({data.get('errcode')})")
            return data.get("account_list") or []

    async def send_text(self, open_kfid: str, external_userid: str, content: str) -> bool:
        """
        发送文本消息给外部联系人（客户）
        - open_kfid: 客服账号ID
        - external_userid: 外部联系人ID（从回调事件中获得）
        """
        token = await self.get_access_token()
        url = f"{self.BASE_URL}/cgi-bin/kf/send_msg"
        params = {"access_token": token}
        payload = {
            "open_kfid": open_kfid,
            "external_userid": external_userid,
            "msgtype": "text",
            "text": {"content": content},
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, params=params, json=payload)
            resp.raise_for_status()
            data = resp.json()
            if data.get("errcode") != 0:
                logger.error(f"客服发送消息失败: {data.get('errmsg')} ({data.get('errcode')})")
                return False
            return True


