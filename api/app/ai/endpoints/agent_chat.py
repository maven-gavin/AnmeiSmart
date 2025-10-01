"""
Agent 对话 API 端点
提供 Agent 对话功能的 HTTP 接口
"""

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.common.infrastructure.db.base import get_db
from app.identity_access.deps import get_current_user
from app.identity_access.infrastructure.db.user import User
from app.ai.schemas.agent_chat import (
    AgentChatRequest,
    AgentConversationCreate,
    AgentConversationUpdate,
    AgentMessageResponse,
    AgentConversationResponse
)
from app.ai.application.agent_chat_service import AgentChatApplicationService
from app.ai.deps import get_agent_chat_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/{agent_config_id}/chat")
async def agent_chat(
    agent_config_id: str,
    request: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service),
    db: Session = Depends(get_db)
):
    """
    Agent 流式对话
    
    支持流式响应，返回 SSE 格式数据
    """
    try:
        return StreamingResponse(
            service.stream_chat(
                agent_config_id=agent_config_id,
                user_id=str(current_user.id),
                message=request.message,
                conversation_id=request.conversation_id,
                inputs=request.inputs
            ),
            media_type="text/event-stream"
        )
    except ValueError as e:
        logger.error(f"Agent 对话参数错误: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Agent 对话失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="对话处理失败")


@router.get("/{agent_config_id}/conversations", response_model=List[AgentConversationResponse])
async def get_agent_conversations(
    agent_config_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """获取 Agent 会话列表"""
    try:
        return await service.get_conversations(
            agent_config_id=agent_config_id,
            user_id=str(current_user.id)
        )
    except Exception as e:
        logger.error(f"获取会话列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取会话列表失败")


@router.post("/{agent_config_id}/conversations", response_model=AgentConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_conversation(
    agent_config_id: str,
    request: AgentConversationCreate,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """创建新会话"""
    try:
        return await service.create_conversation(
            agent_config_id=agent_config_id,
            user_id=str(current_user.id),
            title=request.title
        )
    except Exception as e:
        logger.error(f"创建会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建会话失败")


@router.get("/conversations/{conversation_id}/messages", response_model=List[AgentMessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """获取会话消息历史"""
    try:
        return await service.get_messages(
            conversation_id=conversation_id,
            user_id=str(current_user.id),
            limit=limit
        )
    except ValueError as e:
        logger.error(f"会话不存在或无权访问: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"获取消息历史失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="获取消息历史失败")


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """删除会话"""
    try:
        await service.delete_conversation(
            conversation_id=conversation_id,
            user_id=str(current_user.id)
        )
    except ValueError as e:
        logger.error(f"会话不存在或无权访问: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"删除会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="删除会话失败")


@router.put("/conversations/{conversation_id}", response_model=AgentConversationResponse)
async def update_conversation(
    conversation_id: str,
    request: AgentConversationUpdate,
    current_user: User = Depends(get_current_user),
    service: AgentChatApplicationService = Depends(get_agent_chat_service)
):
    """更新会话"""
    try:
        return await service.update_conversation(
            conversation_id=conversation_id,
            user_id=str(current_user.id),
            title=request.title
        )
    except ValueError as e:
        logger.error(f"会话不存在或无权访问: {e}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"更新会话失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="更新会话失败")

