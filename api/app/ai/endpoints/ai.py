"""
AI服务API端点 - 面向用户的AI功能接口
1. AI聊天对话
2. 获取AI能力信息
3. AI服务健康检查
4. 获取可用AI模型列表

注意：AI配置管理功能在system模块中，仅admin可访问
"""

import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.common.deps import get_db
from app.identity_access.deps.security_deps import get_current_user
from app.identity_access.infrastructure.db.user import User
from app.ai.schemas.ai import (
    AIChatRequest, AIChatResponse, AICapabilitiesResponse, 
    AIHealthStatus, AIProviderInfo
)
from app.ai.ai_service import get_ai_service
from app.chat.application.chat_application_service import ChatApplicationService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/chat", response_model=AIChatResponse, status_code=status.HTTP_200_OK)
async def chat_with_ai(
    request: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    AI聊天对话接口
    面向所有已登录用户，发送消息并获取AI回复
    """
    try:
        logger.info(f"用户 {current_user.id} 发起AI聊天: conversation_id={request.conversation_id}")
        
        # 获取用户角色
        user_role = _get_user_role(current_user)
        
        # 验证会话权限
        chat_service = ChatApplicationService(db)
        conversation = chat_service.get_conversation_by_id(
            conversation_id=request.conversation_id,
            user_id=current_user.id,
            user_role=user_role
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在或无权访问"
            )
        
        # 发送用户消息
        user_message = await chat_service.send_message(
            conversation_id=request.conversation_id,
            content=request.content,
            message_type=request.type,
            sender_id=current_user.id,
            sender_type=user_role
        )
        
        # 获取AI服务并生成回复
        ai_service = get_ai_service(db)
        
        # 获取对话历史
        messages = chat_service.get_conversation_messages(
            conversation_id=request.conversation_id,
            user_id=current_user.id,
            user_role=user_role,
            limit=10  # 获取最近10条消息作为上下文
        )
        
        # 格式化历史记录
        history = []
        for msg in messages:
            history.append({
                "content": msg.content,
                "sender_type": msg.sender_type,
                "timestamp": msg.timestamp.isoformat()
            })
        
        # 获取AI回复
        ai_response = await ai_service.get_response(request.content, history)
        
        # 创建AI回复消息
        ai_message = await chat_service.send_message(
            conversation_id=request.conversation_id,
            content=ai_response.get("content", "抱歉，我暂时无法回复"),
            message_type="text",
            sender_id="ai",
            sender_type="ai"
        )
        
        # 构建响应
        response_data = AIChatResponse(
            id=ai_message.id,
            content=ai_message.content,
            type=ai_message.type,
            conversation_id=request.conversation_id,
            sender={
                "id": "ai",
                "name": "AI助手",
                "avatar": "/avatars/ai.png",
                "type": "ai"
            },
            timestamp=ai_message.timestamp,
            is_read=False,
            is_important=False
        )
        
        logger.info(f"AI聊天完成: message_id={ai_message.id}")
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"AI聊天失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI服务暂时不可用"
        )


@router.get("/capabilities", response_model=AICapabilitiesResponse, status_code=status.HTTP_200_OK)
async def get_ai_capabilities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前可用的AI能力信息
    面向所有已登录用户，返回不包含敏感信息的AI能力列表
    """
    try:
        ai_service = get_ai_service(db)
        
        # 获取可用提供商（不暴露敏感配置）
        available_providers = ai_service.get_available_providers()
        
        provider_infos = []
        for provider_name in available_providers:
            # 获取提供商显示信息
            display_info = _get_provider_display_info(provider_name)
            provider_infos.append(AIProviderInfo(
                name=provider_name,
                display_name=display_info["display_name"],
                is_available=True,
                capabilities=display_info["capabilities"]
            ))
        
        # 获取默认提供商
        default_provider = ai_service.get_default_provider()
        
        # 系统支持的功能
        features = [
            "文本对话",
            "多轮对话",
            "上下文理解", 
            "医美专业咨询",
            "智能推荐"
        ]
        
        return AICapabilitiesResponse(
            available_providers=provider_infos,
            default_provider=default_provider,
            features=features
        )
        
    except Exception as e:
        logger.error(f"获取AI能力失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="无法获取AI能力信息"
        )


@router.get("/health", response_model=AIHealthStatus, status_code=status.HTTP_200_OK)
async def check_ai_health(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    检查AI服务健康状态
    面向所有已登录用户，返回AI服务状态信息
    """
    try:
        ai_service = get_ai_service(db)
        
        # 检查各个提供商状态
        provider_status = await ai_service.check_providers_health()
        
        # 判断整体服务状态
        if all(provider_status.values()):
            overall_status = "healthy"
            message = "AI服务运行正常"
        elif any(provider_status.values()):
            overall_status = "degraded"
            message = "部分AI服务不可用"
        else:
            overall_status = "unhealthy"
            message = "AI服务暂时不可用"
        
        return AIHealthStatus(
            status=overall_status,
            providers=provider_status,
            last_check=datetime.now(),
            message=message
        )
        
    except Exception as e:
        logger.error(f"AI健康检查失败: {e}")
        return AIHealthStatus(
            status="unhealthy",
            providers={},
            last_check=datetime.now(),
            message=f"健康检查失败: {str(e)}"
        )


@router.get("/models", response_model=List[str], status_code=status.HTTP_200_OK)
async def get_available_models(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取当前可用的AI模型列表
    面向所有已登录用户，返回可用模型名称（不包含敏感配置）
    """
    try:
        ai_service = get_ai_service(db)
        models = ai_service.get_available_models()
        
        return models
        
    except Exception as e:
        logger.error(f"获取可用模型失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="无法获取可用模型列表"
        )


# ============ 辅助函数 ============

def _get_user_role(user: User) -> str:
    """获取用户的当前角色"""
    if hasattr(user, '_active_role') and user._active_role:
        return user._active_role
    elif user.roles:
        return user.roles[0].name
    else:
        return 'customer'  # 默认角色


def _get_provider_display_info(provider_name: str) -> Dict[str, Any]:
    """获取AI提供商的显示信息"""
    provider_info = {
        "openai": {
            "display_name": "OpenAI GPT",
            "capabilities": ["文本生成", "对话理解", "多语言支持"]
        },
        "dify": {
            "display_name": "Dify AI",
            "capabilities": ["专业对话", "工作流处理", "知识库检索"]
        },
        "simulated": {
            "display_name": "模拟AI",
            "capabilities": ["基础对话", "医美知识问答"]
        }
    }
    
    return provider_info.get(provider_name, {
        "display_name": provider_name.title(),
        "capabilities": ["基础AI功能"]
    })

