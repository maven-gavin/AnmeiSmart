"""
咨询管理API端点
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models.user import User
from app.api.deps import get_current_user
from app.schemas.chat import ConversationInfo
from app.services.consultation.consultation_service import ConsultationService

router = APIRouter()


@router.post("/sessions", response_model=ConversationInfo)
async def create_consultation_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """客户发起新的咨询会话"""
    consultation_service = ConsultationService(db)
    
    try:
        result = await consultation_service.create_consultation_session(current_user.id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建咨询会话失败")


@router.post("/sessions/{conversation_id}/first-message-task")
async def create_first_message_task(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """客户发送第一条消息后创建咨询待办任务"""
    consultation_service = ConsultationService(db)
    
    try:
        task_id = await consultation_service.create_consultation_task_on_first_message(
            conversation_id, current_user.id
        )
        return {"task_id": task_id, "message": "咨询任务创建成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="创建咨询任务失败")


@router.post("/sessions/{conversation_id}/assign")
async def assign_consultant_to_consultation(
    conversation_id: str,
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """顾问接待咨询会话"""
    consultation_service = ConsultationService(db)
    
    try:
        success = await consultation_service.assign_consultant_to_consultation(
            conversation_id, current_user.id, task_id
        )
        
        if success:
            return {"message": "咨询接待成功"}
        else:
            raise HTTPException(status_code=400, detail="接待失败")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="接待咨询失败")


@router.put("/sessions/{conversation_id}/pin")
async def pin_conversation(
    conversation_id: str,
    pin: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """置顶/取消置顶会话"""
    consultation_service = ConsultationService(db)
    
    try:
        success = await consultation_service.pin_conversation(
            conversation_id, current_user.id, pin
        )
        
        if success:
            action = "置顶" if pin else "取消置顶"
            return {"message": f"会话{action}成功"}
        else:
            raise HTTPException(status_code=400, detail="操作失败")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="会话置顶操作失败")


@router.get("/conversations", response_model=List[ConversationInfo])
async def get_conversations_with_priority(
    include_consultation: bool = True,
    include_friend_chat: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的会话列表（支持置顶排序）"""
    consultation_service = ConsultationService(db)
    
    try:
        result = await consultation_service.get_conversations_with_priority_sorting(
            user_id=current_user.id,
            include_consultation=include_consultation,
            include_friend_chat=include_friend_chat
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail="获取会话列表失败")
