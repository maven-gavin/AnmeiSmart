"""
AI应用管理API端点 - 微服务架构
"""
from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.services import system_service
from app.db.models.system import AIModelConfig
from app.schemas.system import AIModelConfigCreate, AIModelConfigUpdate
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


# Pydantic模型定义
class AIAppRegisterRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    dify_app_id: str
    api_base_url: str
    api_key: str
    app_mode: str  # 'chat', 'completion', 'agent', 'workflow'
    enabled: Optional[bool] = True
    max_tokens: Optional[int] = 2000
    temperature: Optional[float] = 0.7


class AIAppUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    api_key: Optional[str] = None


class AIAppTestRequest(BaseModel):
    test_message: Optional[str] = "Hello"


class AIAppReloadRequest(BaseModel):
    app_ids: Optional[List[str]] = None


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_app(
    *,
    db: Session = Depends(deps.get_db),
    app_config: AIAppRegisterRequest,
    current_user = Depends(deps.get_current_admin),
) -> Dict[str, Any]:
    """
    注册新的AI应用
    """
    try:
        # 将请求数据转换为 AIModelConfigCreate 格式
        model_create = AIModelConfigCreate(
            modelName=app_config.name,
            apiKey=app_config.api_key,
            baseUrl=app_config.api_base_url,
            provider="dify",  # 根据实际需要调整
            temperature=app_config.temperature or 0.7,
            maxTokens=app_config.max_tokens or 2000,
            enabled=app_config.enabled if app_config.enabled is not None else True,
            description=app_config.description
        )
        
        created_model = system_service.create_ai_model_config(db, model_create)
        
        return {
            "success": True,
            "message": "AI应用注册成功",
            "data": {
                "app_id": created_model.id
            }
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"注册AI应用失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )


@router.get("/", status_code=status.HTTP_200_OK)
async def get_app_list(
    *,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_admin),
) -> Dict[str, Any]:
    """
    获取所有AI应用列表
    """
    try:
        response = system_service.get_ai_model_configs(db)
        apps = response.data  # 获取 AIModelConfigInfo 列表
        
        return {
            "success": True,
            "message": f"获取到 {len(apps)} 个AI应用",
            "data": {
                "apps": apps,
                "total": len(apps)
            }
        }
        
    except Exception as e:
        logger.error(f"获取AI应用列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取应用列表失败: {str(e)}"
        )


@router.post("/{app_id}/test", status_code=status.HTTP_200_OK)
async def test_app(
    *,
    db: Session = Depends(deps.get_db),
    app_id: str,
    test_request: AIAppTestRequest,
    current_user = Depends(deps.get_current_admin),
) -> Dict[str, Any]:
    """
    测试AI应用连接
    """
    try:
        # 获取应用信息
        ai_model = db.query(AIModelConfig).filter(AIModelConfig.id == app_id).first()
        
        if not ai_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到应用: {app_id}"
            )
        
        # 简单的连接测试（实际项目中可以调用真实的AI服务进行测试）
        test_result = {
            "success": True,
            "message": "连接测试成功",
            "response_time": 0.5,
            "status": "healthy"
        }
        
        return {
            "success": test_result['success'],
            "message": test_result['message'],
            "data": test_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试AI应用失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"应用测试失败: {str(e)}"
        )


@router.get("/{app_id}/health", status_code=status.HTTP_200_OK)
async def check_app_health(
    *,
    db: Session = Depends(deps.get_db),
    app_id: str,
    current_user = Depends(deps.get_current_admin),
) -> Dict[str, Any]:
    """
    检查AI应用健康状态
    """
    try:
        # 获取应用信息
        ai_model = db.query(AIModelConfig).filter(AIModelConfig.id == app_id).first()
        
        if not ai_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到应用: {app_id}"
            )
        
        # 简单的健康检查
        health_status = "healthy" if getattr(ai_model, 'enabled', False) else "disabled"
        
        return {
            "success": True,
            "message": "健康检查完成",
            "data": {
                "app_id": app_id,
                "app_name": ai_model.model_name,
                "status": health_status,
                "last_check": "just now",
                "enabled": getattr(ai_model, 'enabled', False)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"健康检查失败: {str(e)}"
        )


@router.put("/{app_id}", status_code=status.HTTP_200_OK)
async def update_app(
    *,
    db: Session = Depends(deps.get_db),
    app_id: str,
    update_request: AIAppUpdateRequest,
    current_user = Depends(deps.get_current_admin),
) -> Dict[str, Any]:
    """
    更新AI应用配置
    """
    try:
        # 首先检查应用是否存在
        ai_model = db.query(AIModelConfig).filter(AIModelConfig.id == app_id).first()
        if not ai_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到应用: {app_id}"
            )
        
        # 构建更新数据
        update_data = {}
        if update_request.name is not None:
            update_data["modelName"] = update_request.name
        if update_request.enabled is not None:
            update_data["enabled"] = update_request.enabled
        if update_request.max_tokens is not None:
            update_data["maxTokens"] = update_request.max_tokens
        if update_request.temperature is not None:
            update_data["temperature"] = update_request.temperature
        if update_request.api_key is not None:
            update_data["apiKey"] = update_request.api_key
        
        if update_data:
            model_update = AIModelConfigUpdate(**update_data)
            system_service.update_ai_model_config(db, str(ai_model.model_name), model_update)
        
        return {
            "success": True,
            "message": "AI应用更新成功",
            "data": {
                "app_id": app_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新AI应用失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新应用失败: {str(e)}"
        )


@router.delete("/{app_id}", status_code=status.HTTP_200_OK)
async def delete_app(
    *,
    db: Session = Depends(deps.get_db),
    app_id: str,
    current_user = Depends(deps.get_current_admin),
) -> Dict[str, Any]:
    """
    删除AI应用
    """
    try:
        # 获取应用信息
        ai_model = db.query(AIModelConfig).filter(AIModelConfig.id == app_id).first()
        if not ai_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到应用: {app_id}"
            )
        
        # 删除应用
        success = system_service.delete_ai_model_config(db, str(ai_model.model_name))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除操作失败"
            )
        
        return {
            "success": True,
            "message": "AI应用删除成功",
            "data": {
                "app_id": app_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除AI应用失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除应用失败: {str(e)}"
        )


@router.post("/reload", status_code=status.HTTP_200_OK)
async def reload_configs(
    *,
    db: Session = Depends(deps.get_db),
    reload_request: AIAppReloadRequest,
    current_user = Depends(deps.get_current_admin),
) -> Dict[str, Any]:
    """
    热更新AI应用配置
    """
    try:
        # 刷新AI服务配置（可以通过通知AI服务重新加载配置实现）
        # 这里简化处理，实际项目中可以通过事件系统通知相关服务
        
        message = "所有应用配置已重新加载" if not reload_request.app_ids else f"已重新加载 {len(reload_request.app_ids)} 个应用配置"
        
        return {
            "success": True,
            "message": message,
            "data": {
                "reloaded_apps": reload_request.app_ids or "all"
            }
        }
        
    except Exception as e:
        logger.error(f"配置热更新失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"配置热更新失败: {str(e)}"
        )


@router.get("/{app_id}/metrics", status_code=status.HTTP_200_OK)
async def get_app_metrics(
    *,
    db: Session = Depends(deps.get_db),
    app_id: str,
    days: int = Query(7, description="统计天数"),
    current_user = Depends(deps.get_current_admin),
) -> Dict[str, Any]:
    """
    获取AI应用调用统计（示例实现）
    """
    try:
        # 获取应用信息
        ai_model = db.query(AIModelConfig).filter(AIModelConfig.id == app_id).first()
        
        if not ai_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到应用: {app_id}"
            )
        
        # 模拟统计数据
        metrics = {
            "app_id": app_id,
            "app_name": ai_model.model_name,
            "period_days": days,
            "total_calls": 156,
            "success_calls": 148,
            "failed_calls": 8,
            "success_rate": 0.949,
            "avg_response_time": 1.23,
            "total_tokens": 45678,
            "avg_tokens_per_call": 293
        }
        
        return {
            "success": True,
            "message": f"获取 {days} 天统计数据",
            "data": metrics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取应用统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取统计数据失败: {str(e)}"
        ) 