"""
渠道模块依赖注入
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.deps.database import get_db
from app.channels.services.channel_service import ChannelService
from app.websocket.broadcasting_factory import get_broadcasting_service


async def get_channel_service(db: Session = Depends(get_db)) -> ChannelService:
    """统一的 ChannelService 注入"""
    broadcasting_service = await get_broadcasting_service(db=db)
    return ChannelService(db=db, broadcasting_service=broadcasting_service)
