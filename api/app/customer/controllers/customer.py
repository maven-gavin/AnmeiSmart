"""
客户模块API控制器 - 管理客户及其档案信息
"""
import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from app.identity_access.deps import get_current_user
from app.identity_access.models.user import User
from app.customer.deps.customer import get_customer_service, check_customer_permission
from app.customer.services.customer_service import CustomerService
from app.customer.schemas.customer import (
    CustomerInfo, CustomerProfileInfo, CustomerProfileCreate, 
    CustomerProfileUpdate
)
from app.core.api import BusinessException, ErrorCode

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/", response_model=List[Dict[str, Any]])
async def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    customer_service: CustomerService = Depends(get_customer_service)
):
    """获取客户列表（企业内部用户使用）"""
    try:
        # 检查权限，只有顾问、医生、管理员等可以访问
        if not await check_customer_permission(current_user, ['consultant', 'doctor', 'admin', 'operator']):
            raise HTTPException(status_code=403, detail="无权访问客户列表")
        
        # 调用服务
        customers = customer_service.get_customers(skip, limit)
        return customers
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取客户列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取客户列表失败")


@router.get("/{customer_id}", response_model=CustomerInfo)
async def get_customer(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    customer_service: CustomerService = Depends(get_customer_service)
):
    """获取客户详细信息"""
    try:
        # 检查权限
        if not await check_customer_permission(current_user, ['consultant', 'doctor', 'admin', 'operator']) and current_user.id != customer_id:
            raise HTTPException(status_code=403, detail="无权访问此客户信息")
        
        # 调用服务
        customer = customer_service.get_customer(customer_id)
        if not customer:
            raise HTTPException(status_code=404, detail="客户不存在")
        
        return customer
        
    except HTTPException:
        raise
    except BusinessException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取客户信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取客户信息失败: {str(e)}")


@router.get("/{customer_id}/profile", response_model=CustomerProfileInfo)
async def get_customer_profile(
    customer_id: str,
    current_user: User = Depends(get_current_user),
    customer_service: CustomerService = Depends(get_customer_service)
):
    """获取客户档案信息"""
    try:
        # 检查权限
        if not await check_customer_permission(current_user, ['consultant', 'doctor', 'admin', 'operator']) and current_user.id != customer_id:
            raise HTTPException(status_code=403, detail="无权访问客户档案")
        
        # 调用服务
        profile = customer_service.get_customer_profile(customer_id)
        if not profile:
            raise HTTPException(status_code=404, detail="客户档案不存在")
        
        return profile
        
    except HTTPException:
        raise
    except BusinessException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取客户档案失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取客户档案失败: {str(e)}")


@router.post("/{customer_id}/profile", response_model=CustomerProfileInfo, status_code=status.HTTP_201_CREATED)
async def create_customer_profile(
    customer_id: str,
    profile_data: CustomerProfileCreate,
    current_user: User = Depends(get_current_user),
    customer_service: CustomerService = Depends(get_customer_service)
):
    """创建客户档案"""
    try:
        # 检查权限
        if not await check_customer_permission(current_user, ['consultant', 'doctor', 'admin', 'operator']) and current_user.id != customer_id:
            raise HTTPException(status_code=403, detail="无权创建客户档案")
        
        # 调用服务
        profile = customer_service.create_customer_profile(customer_id, profile_data)
        return profile
    
    except HTTPException:
        raise
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建客户档案失败: {e}")
        raise HTTPException(status_code=500, detail="创建客户档案失败")


@router.put("/{customer_id}/profile", response_model=CustomerProfileInfo)
async def update_customer_profile(
    customer_id: str,
    profile_data: CustomerProfileUpdate,
    current_user: User = Depends(get_current_user),
    customer_service: CustomerService = Depends(get_customer_service)
):
    """更新客户档案"""
    try:
        # 检查权限
        if not await check_customer_permission(current_user, ['consultant', 'doctor', 'admin', 'operator']) and current_user.id != customer_id:
            raise HTTPException(status_code=403, detail="无权更新客户档案")
        
        # 调用服务
        profile = customer_service.update_customer_profile(customer_id, profile_data)
        return profile
    
    except HTTPException:
        raise
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新客户档案失败: {e}")
        raise HTTPException(status_code=500, detail="更新客户档案失败") 