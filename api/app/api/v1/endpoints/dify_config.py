"""
Dify配置管理API端点
支持动态配置Dify应用，无需重启服务
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_admin
from app.schemas.system import (
    DifyConfigCreate, DifyConfigUpdate, DifyConfigInfo, 
    DifyConfigResponse, DifyConfigListResponse
)
from app.services.dify_config_service import (
    create_dify_config, get_dify_configs, get_dify_config,
    update_dify_config, delete_dify_config, test_dify_connection,
    reload_ai_gateway_with_new_config
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/configs", response_model=DifyConfigListResponse)
def get_dify_config_list(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """获取Dify配置列表"""
    try:
        configs = get_dify_configs(db)
        return DifyConfigListResponse(
            success=True,
            data=configs,
            message="获取Dify配置列表成功"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Dify配置列表失败: {str(e)}"
        )


@router.get("/configs/{config_id}", response_model=DifyConfigResponse)
def get_dify_config_detail(
    config_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """获取Dify配置详情"""
    try:
        config = get_dify_config(db, config_id)
        if not config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dify配置不存在"
            )
        
        return DifyConfigResponse(
            success=True,
            data=config,
            message="获取Dify配置详情成功"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取Dify配置详情失败: {str(e)}"
        )


@router.post("/configs", response_model=DifyConfigResponse)
def create_dify_config_endpoint(
    config_data: DifyConfigCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """创建Dify配置"""
    try:
        # 创建配置
        new_config = create_dify_config(db, config_data)
        
        # 动态重载AI Gateway配置
        try:
            reload_ai_gateway_with_new_config()
        except Exception as reload_error:
            # 配置已创建，但重载失败，记录警告
            print(f"Warning: AI Gateway重载失败: {reload_error}")
        
        return DifyConfigResponse(
            success=True,
            data=new_config,
            message="创建Dify配置成功"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建Dify配置失败: {str(e)}"
        )


@router.put("/configs/{config_id}", response_model=DifyConfigResponse)
def update_dify_config_endpoint(
    config_id: str,
    config_data: DifyConfigUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """更新Dify配置"""
    try:
        # 检查配置是否存在
        existing_config = get_dify_config(db, config_id)
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dify配置不存在"
            )
        
        # 更新配置
        updated_config = update_dify_config(db, config_id, config_data)
        
        # 动态重载AI Gateway配置
        try:
            reload_ai_gateway_with_new_config()
        except Exception as reload_error:
            print(f"Warning: AI Gateway重载失败: {reload_error}")
        
        return DifyConfigResponse(
            success=True,
            data=updated_config,
            message="更新Dify配置成功"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新Dify配置失败: {str(e)}"
        )


@router.delete("/configs/{config_id}")
def delete_dify_config_endpoint(
    config_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """删除Dify配置"""
    try:
        # 检查配置是否存在
        existing_config = get_dify_config(db, config_id)
        if not existing_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dify配置不存在"
            )
        
        # 删除配置
        delete_dify_config(db, config_id)
        
        # 动态重载AI Gateway配置
        try:
            reload_ai_gateway_with_new_config()
        except Exception as reload_error:
            print(f"Warning: AI Gateway重载失败: {reload_error}")
        
        return {
            "success": True,
            "message": "删除Dify配置成功"
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除Dify配置失败: {str(e)}"
        )


@router.post("/test-connection")
def test_dify_connection_endpoint(
    config: DifyConfigInfo,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """测试Dify连接"""
    try:
        result = test_dify_connection(config, db)
        
        return {
            "success": result["success"],
            "message": result["message"],
            "details": result.get("details", {})
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"连接测试失败: {str(e)}",
            "details": {}
        }


@router.post("/reload-gateway")
def reload_ai_gateway_endpoint(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_admin)
):
    """手动重载AI Gateway配置"""
    try:
        reload_ai_gateway_with_new_config()
        return {
            "success": True,
            "message": "AI Gateway配置重载成功"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI Gateway配置重载失败: {str(e)}"
        ) 