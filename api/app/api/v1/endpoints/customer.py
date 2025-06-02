"""
客户领域API端点 - 管理客户及其档案信息
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, get_current_user
from app.db.models.user import User, Role
from app.db.models.customer import Customer, CustomerProfile
from app.schemas.customer import (
    CustomerInfo, CustomerProfileInfo, CustomerProfileCreate, 
    CustomerProfileUpdate, RiskNote, ConsultationHistoryItem
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_user_role(user: User) -> str:
    """获取用户的当前角色"""
    if hasattr(user, '_active_role') and user._active_role:
        return user._active_role
    elif user.roles:
        return user.roles[0].name
    else:
        return 'customer'  # 默认角色


@router.get("/", response_model=List[Dict[str, Any]])
async def get_customers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取客户列表（企业内部用户使用）"""
    try:
        # 检查权限，只有顾问、医生、管理员等可以访问
        user_role = get_user_role(current_user)
        if user_role not in ['consultant', 'doctor', 'admin', 'operator']:
            raise HTTPException(status_code=403, detail="无权访问客户列表")
        
        # 查询所有客户用户
        customers_query = db.query(User).join(User.roles).filter(
            Role.name == 'customer',
            User.is_active == True
        )
        
        # 获取客户列表
        customers = customers_query.offset(skip).limit(limit).all()
        
        # 格式化客户数据
        customer_list = []
        for customer in customers:
            # 获取客户的最后一条消息
            from app.db.models.chat import Message, Conversation
            last_message = db.query(Message).join(Conversation).filter(
                Conversation.customer_id == customer.id
            ).order_by(Message.timestamp.desc()).first()
            
            # 计算未读消息数（发给顾问的消息）
            unread_count = db.query(Message).join(Conversation).filter(
                Conversation.customer_id == customer.id,
                Message.sender_type == 'customer',
                Message.is_read == False
            ).count()
            
            # 获取客户标签（从Customer表）
            customer_info = db.query(Customer).filter(Customer.user_id == customer.id).first()
            tags = []
            if customer_info and hasattr(customer_info, 'tags') and customer_info.tags:
                tags = customer_info.tags.split(',') if isinstance(customer_info.tags, str) else customer_info.tags
            
            customer_data = {
                "id": customer.id,
                "name": customer.username,
                "avatar": customer.avatar or '/avatars/user.png',
                "is_online": getattr(customer, 'is_online', False),
                "last_message": {
                    "content": last_message.content if last_message else "",
                    "created_at": last_message.timestamp.isoformat() if last_message else None
                } if last_message else None,
                "unread_count": unread_count,
                "tags": tags,
                "priority": getattr(customer_info, 'priority', 'medium') if customer_info else 'medium',
                "updated_at": customer.updated_at.isoformat() if customer.updated_at else None
            }
            customer_list.append(customer_data)
        
        # 按在线状态和最后消息时间排序
        customer_list.sort(key=lambda x: (
            not x['is_online'],  # 在线用户优先
            x['last_message']['created_at'] if x['last_message'] else '1970-01-01T00:00:00'
        ), reverse=True)
        
        return customer_list
        
    except HTTPException:
        raise  # 重新抛出HTTPException
    except Exception as e:
        logger.error(f"获取客户列表失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取客户列表失败")


@router.get("/{customer_id}", response_model=CustomerInfo)
async def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取客户详细信息"""
    try:
        # 检查权限
        user_role = get_user_role(current_user)
        if user_role not in ['consultant', 'doctor', 'admin', 'operator'] and current_user.id != customer_id:
            raise HTTPException(status_code=403, detail="无权访问此客户信息")
        
        # 验证客户存在
        customer_user = db.query(User).filter(User.id == customer_id).first()
        if not customer_user:
            raise HTTPException(status_code=404, detail="客户不存在")
        
        # 获取客户的扩展信息
        customer = db.query(Customer).filter(Customer.user_id == customer_id).first()
        if not customer:
            raise HTTPException(status_code=404, detail="客户信息不存在")
        
        # 构建基础客户信息响应
        result = {
            "id": customer.id,
            "user_id": customer.user_id,
            "username": customer_user.username,
            "email": customer_user.email,
            "phone": customer_user.phone,
            "avatar": customer_user.avatar,
            "created_at": customer.created_at,
            "updated_at": customer.updated_at,
            "medical_history": customer.medical_history,
            "allergies": customer.allergies,
            "preferences": customer.preferences
        }
        
        # 获取客户档案信息
        profile = db.query(CustomerProfile).filter(
            CustomerProfile.customer_id == customer_id
        ).first()
        
        if profile:
            # 构建profile响应
            result["profile"] = {
                "id": profile.id,
                "basicInfo": {
                    "name": customer_user.username,
                    "age": getattr(customer, "age", None),
                    "gender": getattr(customer, "gender", None),
                    "phone": customer_user.phone
                },
                "medical_history": profile.medical_history,
                "allergies": profile.allergies,
                "preferences": profile.preferences,
                "tags": profile.tags.split(",") if profile.tags else [],
                "riskNotes": profile.risk_notes or [],
                "created_at": profile.created_at,
                "updated_at": profile.updated_at
            }
        
        return result
    except HTTPException:
        raise  # 重新抛出HTTPException
    except Exception as e:
        logger.error(f"获取客户信息失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取客户信息失败: {str(e)}")


@router.get("/{customer_id}/profile", response_model=Dict[str, Any])
async def get_customer_profile(
    customer_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取客户档案信息"""
    try:
        # 检查权限
        user_role = get_user_role(current_user)
        if user_role not in ['consultant', 'doctor', 'admin', 'operator'] and current_user.id != customer_id:
            raise HTTPException(status_code=403, detail="无权访问客户档案")
        
        # 验证客户存在
        customer_user = db.query(User).join(User.roles).filter(
            User.id == customer_id
        ).first()
        
        if not customer_user:
            raise HTTPException(status_code=404, detail="客户不存在")
        
        # 获取客户基础信息
        customer = db.query(Customer).filter(
            Customer.user_id == customer_id
        ).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="客户信息不存在")
        
        # 获取客户档案
        profile = db.query(CustomerProfile).filter(
            CustomerProfile.customer_id == customer_id
        ).first()
        
        if not profile:
            raise HTTPException(status_code=404, detail="客户档案不存在")
        
        # 构建完整的客户档案信息
        result = {
            "id": profile.id,
            "basicInfo": {
                "name": customer_user.username,
                "age": getattr(customer, "age", None),
                "gender": getattr(customer, "gender", None),
                "phone": customer_user.phone
            },
            "medical_history": profile.medical_history,
            "allergies": profile.allergies,
            "preferences": profile.preferences,
            "tags": profile.tags.split(",") if profile.tags else [],
            "riskNotes": profile.risk_notes or []
        }
        
        return result
    except HTTPException:
        raise  # 重新抛出HTTPException
    except Exception as e:
        logger.error(f"获取客户档案失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取客户档案失败: {str(e)}")


@router.post("/{customer_id}/profile", response_model=CustomerProfileInfo, status_code=status.HTTP_201_CREATED)
async def create_customer_profile(
    customer_id: str,
    profile_data: CustomerProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建客户档案"""
    try:
        # 检查权限
        user_role = get_user_role(current_user)
        if user_role not in ['consultant', 'doctor', 'admin', 'operator'] and current_user.id != customer_id:
            raise HTTPException(status_code=403, detail="无权创建客户档案")
        
        # 验证客户存在
        customer = db.query(Customer).filter(
            Customer.user_id == customer_id
        ).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="客户不存在")
        
        # 检查是否已存在档案
        existing_profile = db.query(CustomerProfile).filter(
            CustomerProfile.customer_id == customer_id
        ).first()
        
        if existing_profile:
            raise HTTPException(status_code=400, detail="客户档案已存在")
        
        # 创建新档案
        from app.db.uuid_utils import profile_id
        new_profile = CustomerProfile(
            id=profile_id(),
            customer_id=customer_id,
            medical_history=profile_data.medical_history,
            allergies=profile_data.allergies,
            preferences=profile_data.preferences,
            tags=profile_data.tags
        )
        
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        
        # 获取用户信息以构建响应
        user = db.query(User).filter(User.id == customer_id).first()
        
        # 构建响应
        result = {
            "id": new_profile.id,
            "basicInfo": {
                "name": user.username,
                "phone": user.phone
            },
            "medical_history": new_profile.medical_history,
            "allergies": new_profile.allergies,
            "preferences": new_profile.preferences,
            "tags": new_profile.tags.split(",") if new_profile.tags else [],
            "riskNotes": []
        }
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建客户档案失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="创建客户档案失败")


@router.put("/{customer_id}/profile", response_model=CustomerProfileInfo)
async def update_customer_profile(
    customer_id: str,
    profile_data: CustomerProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新客户档案"""
    try:
        # 检查权限
        user_role = get_user_role(current_user)
        if user_role not in ['consultant', 'doctor', 'admin', 'operator'] and current_user.id != customer_id:
            raise HTTPException(status_code=403, detail="无权更新客户档案")
        
        # 验证客户存在
        customer = db.query(Customer).filter(
            Customer.user_id == customer_id
        ).first()
        
        if not customer:
            raise HTTPException(status_code=404, detail="客户不存在")
        
        # 获取档案
        profile = db.query(CustomerProfile).filter(
            CustomerProfile.customer_id == customer_id
        ).first()
        
        if not profile:
            raise HTTPException(status_code=404, detail="客户档案不存在")
        
        # 更新档案
        if profile_data.medical_history is not None:
            profile.medical_history = profile_data.medical_history
        
        if profile_data.allergies is not None:
            profile.allergies = profile_data.allergies
        
        if profile_data.preferences is not None:
            profile.preferences = profile_data.preferences
        
        if profile_data.tags is not None:
            profile.tags = profile_data.tags
        
        if profile_data.risk_notes is not None:
            profile.risk_notes = [note.model_dump() for note in profile_data.risk_notes]
        
        # 更新时间戳
        profile.updated_at = datetime.now()
        
        db.commit()
        db.refresh(profile)
        
        # 获取用户信息以构建响应
        user = db.query(User).filter(User.id == customer_id).first()
        
        # 构建响应
        result = {
            "id": profile.id,
            "basicInfo": {
                "name": user.username,
                "phone": user.phone
            },
            "medical_history": profile.medical_history,
            "allergies": profile.allergies,
            "preferences": profile.preferences,
            "tags": profile.tags.split(",") if profile.tags else [],
            "riskNotes": profile.risk_notes or [],
            "created_at": profile.created_at,
            "updated_at": profile.updated_at
        }
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新客户档案失败: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="更新客户档案失败") 