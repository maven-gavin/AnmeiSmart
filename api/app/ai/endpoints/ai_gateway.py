"""
AI Gateway管理API端点

提供AI Gateway的管理、监控和配置功能。
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.common.infrastructure.db.base import get_db
from app.identity_access.deps import get_current_user
from app.identity_access.infrastructure.db.user import User
from app.ai.ai_gateway_service import get_ai_gateway_service
from app.ai.interfaces import AIScenario

router = APIRouter()
logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """聊天请求"""
    message: str = Field(..., description="用户消息")
    session_id: Optional[str] = Field(None, description="会话ID")
    scenario: Optional[str] = Field("general_chat", description="使用场景")
    context: Optional[Dict[str, Any]] = Field(None, description="额外上下文")


class BeautyPlanRequest(BaseModel):
    """医美方案请求"""
    requirements: str = Field(..., description="方案需求")
    user_profile: Dict[str, Any] = Field(..., description="用户档案")
    budget_range: Optional[str] = Field(None, description="预算范围")
    timeline: Optional[str] = Field(None, description="期望时间")


class SummaryRequest(BaseModel):
    """总结请求"""
    content: str = Field(..., description="待总结内容")
    summary_type: Optional[str] = Field("detailed", description="总结类型")


class SentimentRequest(BaseModel):
    """情感分析请求"""
    text: str = Field(..., description="待分析文本")


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    providers: Dict[str, Any]
    cache_stats: Optional[Dict[str, Any]] = None
    timestamp: str


@router.post("/chat", summary="AI聊天")
async def ai_chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    通用AI聊天接口
    
    支持不同场景的智能对话：
    - general_chat: 通用聊天
    - customer_service: 客服对话
    - medical_advice: 医疗咨询
    """
    try:
        ai_gateway = get_ai_gateway_service(db)
        
        # 构建用户档案
        user_profile = {
            "user_id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "roles": [role.name for role in current_user.roles]
        }
        
        # 调用AI Gateway
        response = await ai_gateway.chat(
            message=request.message,
            user_id=str(current_user.id),
            session_id=request.session_id or f"chat_{current_user.id}",
            user_profile=user_profile
        )
        
        return {
            "success": response.success,
            "content": response.content,
            "provider": response.provider.value,
            "scenario": response.scenario.value,
            "response_time": response.response_time,
            "usage": response.usage,
            "metadata": response.metadata
        }
        
    except Exception as e:
        logger.error(f"AI聊天请求失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI聊天服务暂时不可用: {str(e)}"
        )


@router.post("/beauty-plan", summary="生成医美方案")
async def generate_beauty_plan(
    request: BeautyPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    生成个性化医美方案
    
    根据用户需求和档案信息，生成详细的医美治疗方案。
    """
    try:
        ai_gateway = get_ai_gateway_service(db)
        
        # 增强用户档案信息
        enhanced_profile = {
            **request.user_profile,
            "user_id": str(current_user.id),
            "username": current_user.username,
            "budget_range": request.budget_range,
            "timeline": request.timeline
        }
        
        response = await ai_gateway.generate_beauty_plan(
            requirements=[request.requirements],  # 将字符串转换为列表
            user_id=str(current_user.id),
            user_profile=enhanced_profile
        )
        
        return {
            "success": response.success,
            "content": response.content,
            "provider": response.provider.value,
            "plan_sections": response.plan_sections,
            "estimated_cost": response.estimated_cost,
            "timeline": response.timeline,
            "risks": response.risks,
            "response_time": response.response_time,
            "usage": response.usage
        }
        
    except Exception as e:
        logger.error(f"医美方案生成失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"方案生成服务暂时不可用: {str(e)}"
        )


@router.post("/summarize", summary="总结咨询内容")
async def summarize_consultation(
    request: SummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    总结咨询对话内容
    
    分析咨询对话，提取关键信息和行动项。
    """
    try:
        ai_gateway = get_ai_gateway_service(db)
        
        response = await ai_gateway.summarize_consultation(
            conversation_text=request.content,
            user_id=str(current_user.id)
        )
        
        return {
            "success": response.success,
            "content": response.content,
            "provider": response.provider.value,
            "key_points": response.key_points,
            "action_items": response.action_items,
            "sentiment_score": response.sentiment_score,
            "categories": response.categories,
            "response_time": response.response_time,
            "usage": response.usage
        }
        
    except Exception as e:
        logger.error(f"咨询总结失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"总结服务暂时不可用: {str(e)}"
        )


@router.post("/sentiment", summary="情感分析")
async def analyze_sentiment(
    request: SentimentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    分析文本情感倾向
    
    识别文本的情感倾向和强度。
    """
    try:
        ai_gateway = get_ai_gateway_service(db)
        
        response = await ai_gateway.analyze_sentiment(
            text=request.text,
            user_id=str(current_user.id)
        )
        
        return {
            "success": response.success,
            "content": response.content,
            "provider": response.provider.value,
            "sentiment_score": response.sentiment_score,
            "confidence": response.confidence,
            "emotions": response.emotions,
            "response_time": response.response_time,
            "usage": response.usage
        }
        
    except Exception as e:
        logger.error(f"情感分析失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"情感分析服务暂时不可用: {str(e)}"
        )


@router.get("/health", response_model=HealthResponse, summary="健康检查")
async def get_health_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取AI Gateway健康状态
    
    检查所有AI服务提供商的健康状态和性能指标。
    """
    try:
        ai_gateway = get_ai_gateway_service(db)
        health_data = await ai_gateway.get_health_status()
        
        return HealthResponse(
            status=health_data.get("gateway_status", "unknown"),
            providers=health_data.get("providers", {}),
            cache_stats=health_data.get("cache_stats"),
            timestamp=health_data.get("timestamp", "")
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"健康检查服务不可用: {str(e)}"
        )


@router.post("/reload", summary="重新加载配置")
async def reload_configuration(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    重新加载AI Gateway配置
    
    重新初始化所有AI服务提供商和路由配置。
    需要管理员权限。
    """
    # 检查管理员权限
    from app.identity_access.deps.permission_deps import is_user_admin
    if not await is_user_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    try:
        from app.services.ai.ai_gateway_service import reload_ai_gateway_service
        reload_ai_gateway_service()
        
        from datetime import datetime
        
        return {
            "success": True,
            "message": "AI Gateway配置重新加载成功",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"配置重新加载失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"配置重新加载失败: {str(e)}"
        )


@router.get("/scenarios", summary="获取支持的场景")
async def get_supported_scenarios(
    current_user: User = Depends(get_current_user)
):
    """
    获取AI Gateway支持的所有使用场景
    """
    scenarios = []
    for scenario in AIScenario:
        scenarios.append({
            "value": scenario.value,
            "name": scenario.name,
            "description": _get_scenario_description(scenario)
        })
    
    return {
        "scenarios": scenarios,
        "total": len(scenarios)
    }


def _get_scenario_description(scenario: AIScenario) -> str:
    """获取场景描述"""
    descriptions = {
        AIScenario.GENERAL_CHAT: "通用聊天对话",
        AIScenario.BEAUTY_PLAN: "个性化医美方案生成",
        AIScenario.CONSULTATION_SUMMARY: "咨询对话总结分析",
        AIScenario.SENTIMENT_ANALYSIS: "文本情感倾向分析",
        AIScenario.CUSTOMER_SERVICE: "智能客服支持",
        AIScenario.MEDICAL_ADVICE: "医疗建议咨询"
    }
    return descriptions.get(scenario, "未知场景")


@router.get("/providers", summary="获取AI服务提供商信息")
async def get_providers_info(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取所有已配置的AI服务提供商信息
    """
    try:
        ai_gateway = get_ai_gateway_service(db)
        
        # 获取所有注册的服务提供商信息
        providers_info = {}
        
        if ai_gateway.gateway and ai_gateway.gateway.service_instances:
            for provider, service in ai_gateway.gateway.service_instances.items():
                try:
                    info = await service.get_provider_info()
                    providers_info[provider.value] = info
                except Exception as e:
                    providers_info[provider.value] = {
                        "provider": provider.value,
                        "status": "error",
                        "error": str(e)
                    }
        
        return {
            "providers": providers_info,
            "total": len(providers_info)
        }
        
    except Exception as e:
        logger.error(f"获取提供商信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取提供商信息失败: {str(e)}"
        ) 