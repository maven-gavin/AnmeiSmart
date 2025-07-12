"""
AI辅助方案生成API端点
提供完整的方案生成流程API：会话管理、信息分析、方案生成、优化迭代
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.services.plan_generation.plan_generation_service import PlanGenerationService
from app.services.plan_generation.info_analysis_service import InfoAnalysisService
from app.services.plan_generation.plan_optimization_service import PlanOptimizationService
from app.services.plan_generation.plan_version_service import PlanVersionService
from app.schemas.plan_generation import (
    PlanGenerationSessionCreate,
    PlanGenerationSessionInfo,
    PlanDraftInfo,
    GeneratePlanRequest,
    OptimizePlanRequest,
    AnalyzeInfoRequest,
    GenerateGuidanceRequest,
    PlanGenerationResponse,
    InfoAnalysisResponse,
    PlanVersionCompareResponse,
    PlanSessionStatus,
    PlanDraftStatus
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def get_user_role(user: User) -> str:
    """获取用户角色"""
    if hasattr(user, '_active_role') and user._active_role:
        return user._active_role
    elif user.roles:
        return user.roles[0].name
    return 'consultant'


# ===== 会话管理 =====

@router.post("/sessions", response_model=PlanGenerationSessionInfo, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_data: PlanGenerationSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建方案生成会话"""
    try:
        service = PlanGenerationService(db)
        
        # 验证用户权限（只有顾问可以创建会话）
        user_role = get_user_role(current_user)
        if user_role not in ['consultant', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有顾问和管理员可以创建方案生成会话"
            )
        
        session = service.create_session(
            conversation_id=session_data.conversation_id,
            customer_id=session_data.customer_id,
            consultant_id=current_user.id,
            session_metadata=session_data.session_metadata
        )
        
        return session
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"创建方案生成会话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="创建会话失败"
        )


@router.get("/sessions/{session_id}", response_model=PlanGenerationSessionInfo)
async def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取方案生成会话详情"""
    try:
        service = PlanGenerationService(db)
        session = service.get_session(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="方案生成会话不存在"
            )
        
        # 权限检查：只有相关的顾问或客户可以查看
        user_role = get_user_role(current_user)
        if user_role not in ['admin'] and current_user.id not in [session.consultant_id, session.customer_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问该会话"
            )
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取方案生成会话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话失败"
        )


@router.get("/sessions/conversation/{conversation_id}", response_model=Optional[PlanGenerationSessionInfo])
async def get_session_by_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据对话ID获取方案生成会话"""
    try:
        service = PlanGenerationService(db)
        session = service.get_session_by_conversation(conversation_id)
        
        if not session:
            return None
        
        # 权限检查
        user_role = get_user_role(current_user)
        if user_role not in ['admin'] and current_user.id not in [session.consultant_id, session.customer_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问该会话"
            )
        
        return session
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"根据对话ID获取会话失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取会话失败"
        )


# ===== 信息分析 =====

@router.post("/analyze-info", response_model=InfoAnalysisResponse)
async def analyze_conversation_info(
    request: AnalyzeInfoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """分析对话信息完整性"""
    try:
        service = InfoAnalysisService(db)
        
        # 验证会话访问权限
        plan_service = PlanGenerationService(db)
        session = plan_service.get_session_by_conversation(request.conversation_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="方案生成会话不存在"
            )
        
        # 权限检查
        user_role = get_user_role(current_user)
        if user_role not in ['admin'] and current_user.id not in [session.consultant_id, session.customer_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问该会话"
            )
        
        analysis = await service.analyze_conversation_info(
            session.id,
            force_analysis=request.force_analysis
        )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分析对话信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分析信息失败"
        )


@router.post("/generate-guidance", response_model=Dict[str, Any])
async def generate_guidance_questions(
    request: GenerateGuidanceRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成引导问题"""
    try:
        service = InfoAnalysisService(db)
        
        # 验证会话访问权限
        plan_service = PlanGenerationService(db)
        session = plan_service.get_session_by_conversation(request.conversation_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="方案生成会话不存在"
            )
        
        # 权限检查
        user_role = get_user_role(current_user)
        if user_role not in ['admin'] and current_user.id not in [session.consultant_id, session.customer_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问该会话"
            )
        
        guidance = await service.generate_guidance_questions(
            session.id,
            request.missing_categories,
            request.context
        )
        
        return {"guidance_questions": guidance}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成引导问题失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成引导问题失败"
        )


# ===== 方案生成 =====

@router.post("/generate", response_model=PlanGenerationResponse)
async def generate_plan(
    request: GeneratePlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """生成方案"""
    try:
        service = PlanGenerationService(db)
        
        # 验证用户权限（只有顾问可以生成方案）
        user_role = get_user_role(current_user)
        if user_role not in ['consultant', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有顾问和管理员可以生成方案"
            )
        
        # 验证会话存在
        session = service.get_session_by_conversation(request.conversation_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="方案生成会话不存在"
            )
        
        # 权限检查
        if current_user.id != session.consultant_id and user_role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有会话的顾问可以生成方案"
            )
        
        response = await service.generate_plan(request, current_user.id)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成方案失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="生成方案失败"
        )


@router.post("/optimize", response_model=PlanDraftInfo)
async def optimize_plan(
    request: OptimizePlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """优化方案"""
    try:
        service = PlanOptimizationService(db)
        
        # 验证用户权限
        user_role = get_user_role(current_user)
        if user_role not in ['consultant', 'admin']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有顾问和管理员可以优化方案"
            )
        
        # TODO: 添加更详细的权限检查（验证草稿归属）
        
        optimized_draft = await service.optimize_plan(request, current_user.id)
        
        return optimized_draft
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"优化方案失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="优化方案失败"
        )


# ===== 草稿管理 =====

@router.get("/sessions/{session_id}/drafts", response_model=List[PlanDraftInfo])
async def get_session_drafts(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话的所有草稿"""
    try:
        service = PlanGenerationService(db)
        
        # 验证会话存在和权限
        session = service.get_session(session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="方案生成会话不存在"
            )
        
        # 权限检查
        user_role = get_user_role(current_user)
        if user_role not in ['admin'] and current_user.id not in [session.consultant_id, session.customer_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问该会话的草稿"
            )
        
        drafts = service.get_session_drafts(session_id)
        
        return drafts
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取会话草稿失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取草稿失败"
        )


@router.get("/drafts/{draft_id}", response_model=PlanDraftInfo)
async def get_draft(
    draft_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取草稿详情"""
    try:
        service = PlanGenerationService(db)
        draft = service.get_draft(draft_id)
        
        if not draft:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="方案草稿不存在"
            )
        
        # 权限检查：通过会话验证权限
        session = service.get_session(draft.session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="关联的方案生成会话不存在"
            )
        
        user_role = get_user_role(current_user)
        if user_role not in ['admin'] and current_user.id not in [session.consultant_id, session.customer_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="无权限访问该草稿"
            )
        
        return draft
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取草稿详情失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取草稿失败"
        )


# ===== 版本管理 =====

@router.get("/sessions/{session_id}/versions", response_model=List[PlanDraftInfo])
async def get_session_versions(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话的所有版本"""
    try:
        service = PlanVersionService(db)
        
        # TODO: 添加权限检查
        
        versions = service.get_draft_versions(session_id)
        
        return versions
        
    except Exception as e:
        logger.error(f"获取会话版本失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取版本失败"
        )


@router.post("/sessions/{session_id}/compare", response_model=PlanVersionCompareResponse)
async def compare_session_versions(
    session_id: str,
    version_numbers: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """比较会话版本"""
    try:
        service = PlanVersionService(db)
        
        # TODO: 添加权限检查
        
        if len(version_numbers) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="版本比较需要提供两个版本号"
            )
        
        comparison = service.compare_versions(session_id, version_numbers[0], version_numbers[1])
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"比较会话版本失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="版本比较失败"
        )


# ===== 统计和监控 =====

@router.get("/stats", response_model=Dict[str, Any])
async def get_generation_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取方案生成统计信息"""
    try:
        service = PlanGenerationService(db)
        
        # 只有管理员可以查看统计信息
        user_role = get_user_role(current_user)
        if user_role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="只有管理员可以查看统计信息"
            )
        
        stats = service.get_generation_stats()
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取统计信息失败"
        ) 