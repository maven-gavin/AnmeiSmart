"""
AI服务API端点:负责与AI进行对话
1. 根据用户输入的多模态内容，生成AI回复
2. 获取与AI的对话历史
3. 选择历史对话，追加到当前对话中，继续对话


"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.base import get_db
from app.db.models.user import User
from app.db.models.chat import Conversation, Message
from app.schemas.chat import AIChatRequest, MessageInfo
from app.core.security import get_current_user, check_role_permission
from app.services.ai import get_ai_service
from app.services.chat import ChatService, MessageService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

