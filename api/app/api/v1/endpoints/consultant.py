from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.consultant import (
    PersonalizedPlanResponse, PersonalizedPlanCreate, PersonalizedPlanUpdate,
    ProjectTypeResponse, ProjectTemplateResponse,
    RecommendationRequest, RecommendationResponse
)
from app.schemas.user import UserResponse
from app.services.consultant_service import ConsultantService
# 移除自定义异常导入，直接使用HTTPException

router = APIRouter()


@router.get("/plans", response_model=List[PersonalizedPlanResponse])
async def get_all_plans(
    consultant_id: Optional[str] = Query(None, description="筛选特定顾问的方案"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取所有个性化方案"""
    try:
        service = ConsultantService(db)
        return service.get_all_plans(consultant_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取方案列表失败: {str(e)}"
        )


@router.get("/plans/{plan_id}", response_model=PersonalizedPlanResponse)
async def get_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """根据ID获取个性化方案详情"""
    try:
        service = ConsultantService(db)
        return service.get_plan_by_id(plan_id)
    except HTTPException:
        raise  # 重新抛出HTTPException
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取方案详情失败: {str(e)}"
        )


@router.get("/customers/{customer_id}/plans", response_model=List[PersonalizedPlanResponse])
async def get_customer_plans(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取客户的所有方案"""
    try:
        service = ConsultantService(db)
        return service.get_customer_plans(customer_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取客户方案失败: {str(e)}"
        )


@router.post("/plans", response_model=PersonalizedPlanResponse)
async def create_plan(
    plan_data: PersonalizedPlanCreate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """创建个性化方案"""
    try:
        service = ConsultantService(db)
        
        # 从当前用户信息获取顾问ID和姓名
        consultant_id = current_user.id
        consultant_name = current_user.username  # 或者从顾问扩展信息获取
        
        return service.create_plan(plan_data, consultant_id, consultant_name)
    except HTTPException:
        raise  # 重新抛出HTTPException
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建方案失败: {str(e)}"
        )


@router.put("/plans/{plan_id}", response_model=PersonalizedPlanResponse)
async def update_plan(
    plan_id: str,
    plan_data: PersonalizedPlanUpdate,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """更新个性化方案"""
    try:
        service = ConsultantService(db)
        return service.update_plan(plan_id, plan_data)
    except HTTPException:
        raise  # 重新抛出HTTPException
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新方案失败: {str(e)}"
        )


@router.delete("/plans/{plan_id}")
async def delete_plan(
    plan_id: str,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """删除个性化方案"""
    try:
        service = ConsultantService(db)
        success = service.delete_plan(plan_id)
        if success:
            return {"message": "方案删除成功"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="删除方案失败"
            )
    except HTTPException:
        raise  # 重新抛出HTTPException
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除方案失败: {str(e)}"
        )


@router.get("/project-types", response_model=List[ProjectTypeResponse])
async def get_project_types(
    active_only: bool = Query(True, description="是否只返回激活的项目类型"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取所有项目类型"""
    try:
        service = ConsultantService(db)
        return service.get_all_project_types(active_only)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目类型失败: {str(e)}"
        )


@router.get("/project-templates", response_model=List[ProjectTemplateResponse])
async def get_project_templates(
    category: Optional[str] = Query(None, description="项目分类筛选"),
    active_only: bool = Query(True, description="是否只返回激活的模板"),
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """获取所有项目模板"""
    try:
        service = ConsultantService(db)
        return service.get_all_project_templates(category, active_only)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取项目模板失败: {str(e)}"
        )


@router.post("/recommendations", response_model=RecommendationResponse)
async def generate_recommendations(
    request: RecommendationRequest,
    db: Session = Depends(get_db),
    current_user: UserResponse = Depends(get_current_user)
):
    """生成个性化方案推荐"""
    try:
        service = ConsultantService(db)
        return service.generate_recommendations(request)
    except HTTPException:
        raise  # 重新抛出HTTPException
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"生成推荐失败: {str(e)}"
        ) 