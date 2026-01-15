"""
渠道模块依赖注入
"""
from __future__ import annotations

import os
import logging
from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.deps.database import get_db
from app.channels.services.channel_service import ChannelService
from app.channels.services.channel_identity_service import ChannelIdentityService
from app.channels.services.channel_config_service import ChannelConfigService
from app.websocket.broadcasting_factory import get_broadcasting_service
from app.channels.adapters.wechat_work.adapter import WeChatWorkAdapter

logger = logging.getLogger(__name__)


async def get_channel_service(db: Session = Depends(get_db)) -> ChannelService:
    """统一的 ChannelService 注入（确保适配器已注册）"""
    broadcasting_service = await get_broadcasting_service(db=db)
    service = ChannelService(db=db, broadcasting_service=broadcasting_service)

    # ============ 企业微信（应用消息） ============
    corp_id = os.getenv("WECHAT_WORK_CORP_ID", "")
    agent_id = os.getenv("WECHAT_WORK_AGENT_ID", "")
    secret = os.getenv("WECHAT_WORK_SECRET", "")
    token = os.getenv("WECHAT_WORK_TOKEN", "")
    encoding_aes_key = os.getenv("WECHAT_WORK_ENCODING_AES_KEY", "")

    if corp_id and agent_id and secret:
        service.register_adapter(
            "wechat_work",
            WeChatWorkAdapter(
                {
                    "corp_id": corp_id,
                    "agent_id": agent_id,
                    "secret": secret,
                    "token": token,
                    "encoding_aes_key": encoding_aes_key,
                }
            ),
        )

    # ============ 企业微信（微信客服） ============
    # 注意：客服的 secret/token/encodingAESKey 通常独立于自建应用
    kf_secret = os.getenv("WECHAT_WORK_KF_SECRET", "")
    kf_token = os.getenv("WECHAT_WORK_KF_TOKEN", "")
    kf_encoding_aes_key = os.getenv("WECHAT_WORK_KF_ENCODING_AES_KEY", "")
    kf_open_kfid = os.getenv("WECHAT_WORK_KF_OPEN_KFID", "")

    # open_kfid 只在“发送外部消息”时必需；收回调/建会话不依赖 open_kfid
    if corp_id and kf_secret:
        from app.channels.adapters.wechat_work.kf_adapter import WeChatWorkKfAdapter

        service.register_adapter(
            "wechat_work_kf",
            WeChatWorkKfAdapter(
                {
                    "corp_id": corp_id,
                    "secret": kf_secret,
                    "token": kf_token,
                    "encoding_aes_key": kf_encoding_aes_key,
                    "open_kfid": kf_open_kfid or None,
                }
            ),
        )
    else:
        if kf_open_kfid or kf_secret:
            logger.warning("检测到部分客服配置，但不完整，未注册 wechat_work_kf 适配器")

    return service


def get_channel_identity_service(db: Session = Depends(get_db)) -> ChannelIdentityService:
    """ChannelIdentityService 注入"""
    return ChannelIdentityService(db=db)


def get_channel_config_service(db: Session = Depends(get_db)) -> ChannelConfigService:
    """ChannelConfigService 注入"""
    return ChannelConfigService(db=db)

