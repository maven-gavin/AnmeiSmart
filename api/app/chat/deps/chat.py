"""
聊天模块依赖注入配置

遵循新架构标准：
- 使用FastAPI的依赖注入避免循环依赖
- 直接使用Service层，无需Repository抽象
"""

import logging
from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.chat.services.chat_service import ChatService
from app.websocket.broadcasting_factory import get_broadcasting_service_dependency
from app.websocket.broadcasting_service import BroadcastingService

logger = logging.getLogger(__name__)


async def get_chat_service(
    db: Session = Depends(get_db),
    broadcasting_service: Optional[BroadcastingService] = Depends(get_broadcasting_service_dependency)
) -> ChatService:
    """获取聊天服务实例"""
    logger.info("依赖注入：开始创建ChatService")
    service = ChatService(db=db, broadcasting_service=broadcasting_service)
    logger.info("依赖注入：ChatService创建成功")
    return service
