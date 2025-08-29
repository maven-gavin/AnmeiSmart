"""
咨询总结API端点
提供咨询总结的创建、更新、查询等功能
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.services.consultation.consultation_summary_service import ConsultationSummaryService
from app.schemas.chat import (
    ConsultationSummaryResponse,
    ConsultationSummaryInfo,
    CreateConsultationSummaryRequest,
    UpdateConsultationSummaryRequest,
    AIGenerateSummaryRequest
)

router = APIRouter()


@router.get("/conversation/{conversation_id}/summary", response_model=ConsultationSummaryResponse)
def get_consultation_summary(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取会话的咨询总结"""
    service = ConsultationSummaryService(db)
    
    try:
        result = service.get_conversation_summary(conversation_id, current_user.id)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="会话不存在或无权限访问"
            )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/conversation/{conversation_id}/summary", response_model=ConsultationSummaryResponse)
def create_consultation_summary(
    conversation_id: str,
    request: CreateConsultationSummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建咨询总结"""
    service = ConsultationSummaryService(db)
    
    # 验证请求中的conversation_id与URL中的一致
    if request.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请求中的会话ID与URL不匹配"
        )
    
    try:
        return service.create_consultation_summary(request, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/conversation/{conversation_id}/summary", response_model=ConsultationSummaryResponse)
def update_consultation_summary(
    conversation_id: str,
    request: UpdateConsultationSummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新咨询总结"""
    service = ConsultationSummaryService(db)
    
    try:
        return service.update_consultation_summary(conversation_id, request, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/conversation/{conversation_id}/summary")
def delete_consultation_summary(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除咨询总结"""
    service = ConsultationSummaryService(db)
    
    try:
        service.delete_consultation_summary(conversation_id, current_user.id)
        return {"message": "咨询总结已删除"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/conversation/{conversation_id}/summary/ai-generate")
async def ai_generate_summary(
    conversation_id: str,
    request: AIGenerateSummaryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """AI生成咨询总结"""
    service = ConsultationSummaryService(db)
    
    # 验证请求中的conversation_id与URL中的一致
    if request.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="请求中的会话ID与URL不匹配"
        )
    
    try:
        return await service.ai_generate_summary(request, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/conversation/{conversation_id}/summary/ai-save", response_model=ConsultationSummaryResponse)
def save_ai_generated_summary(
    conversation_id: str,
    ai_summary: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """保存AI生成的咨询总结"""
    service = ConsultationSummaryService(db)
    
    try:
        return service.save_ai_generated_summary(conversation_id, ai_summary, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/customer/{customer_id}/consultation-history", response_model=List[ConsultationSummaryInfo])
def get_customer_consultation_history(
    customer_id: str,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取客户的咨询历史总结"""
    service = ConsultationSummaryService(db)
    
    try:
        return service.get_customer_consultation_history(customer_id, current_user.id, limit)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        ) 