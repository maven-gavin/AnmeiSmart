"""
客户服务 - 核心业务逻辑
处理客户CRUD、客户档案管理等功能
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from app.customer.models.customer import Customer, CustomerProfile
from app.customer.schemas.customer import (
    CustomerInfo, CustomerProfileInfo, CustomerProfileCreate, CustomerProfileUpdate
)
from app.identity_access.models.user import User
from app.chat.models.chat import Message, Conversation
from app.core.api import BusinessException, ErrorCode

logger = logging.getLogger(__name__)


class CustomerService:
    """客户服务 - 直接操作数据库模型"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_customers(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """获取客户列表，包含用户信息和聊天统计"""
        # 查询客户用户
        from app.identity_access.enums import UserStatus
        customers_query = self.db.query(User).join(User.roles).filter(
            User.status == UserStatus.ACTIVE
        )
        
        customers = customers_query.offset(skip).limit(limit).all()
        
        customer_list = []
        for customer_user in customers:
            # 获取客户的最后一条消息
            last_message = self.db.query(Message).join(Conversation).filter(
                Conversation.owner_id == customer_user.id
            ).order_by(Message.timestamp.desc()).first()
            
            # 计算未读消息数
            unread_count = self.db.query(Message).join(Conversation).filter(
                Conversation.owner_id == customer_user.id,
                Message.sender_type == 'customer',
                Message.is_read == False
            ).count()
            
            # 获取客户扩展信息
            customer_info = self.db.query(Customer).filter(
                Customer.user_id == customer_user.id
            ).first()
            
            tags = []
            if customer_info and hasattr(customer_info, 'tags') and customer_info.tags:
                tags = customer_info.tags.split(',') if isinstance(customer_info.tags, str) else customer_info.tags
            
            customer_data = {
                "id": customer_user.id,
                "name": customer_user.username,
                "avatar": customer_user.avatar or '/avatars/user.png',
                "is_online": getattr(customer_user, 'is_online', False),
                "last_message": {
                    "content": last_message.content if last_message else "",
                    "created_at": last_message.timestamp.isoformat() if last_message else None
                } if last_message else None,
                "unread_count": unread_count,
                "tags": tags,
                "priority": getattr(customer_info, 'priority', 'medium') if customer_info else 'medium',
                "updated_at": customer_user.updated_at.isoformat() if customer_user.updated_at else None
            }
            customer_list.append(customer_data)
        
        # 按在线状态和最后消息时间排序
        customer_list.sort(key=lambda x: (
            not x['is_online'],  # 在线用户优先
            x['last_message']['created_at'] if x['last_message'] else '1970-01-01T00:00:00'
        ), reverse=True)
        
        return customer_list
    
    def get_customer(self, customer_id: str) -> Optional[CustomerInfo]:
        """获取客户详细信息"""
        # 获取用户信息
        user = self.db.query(User).filter(User.id == customer_id).first()
        if not user:
            return None
        
        # 获取客户扩展信息
        customer = self.db.query(Customer).filter(
            Customer.user_id == customer_id
        ).first()
        
        if not customer:
            return None
        
        # 获取客户档案
        profile = self.db.query(CustomerProfile).filter(
            CustomerProfile.customer_id == customer_id
        ).first()
        
        # 构建响应 - 合并用户和客户信息
        customer_dict = {
            "id": user.id,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "avatar": user.avatar,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "medical_history": customer.medical_history if customer else None,
            "allergies": customer.allergies if customer else None,
            "preferences": customer.preferences if customer else None,
        }
        
        customer_info = CustomerInfo(**customer_dict)
        
        # 填充客户档案
        if profile:
            # 需要手动构建profile_info，因为schema结构复杂
            from app.customer.schemas.customer import CustomerBasicInfo
            profile_info = CustomerProfileInfo(
                id=profile.id,
                basicInfo=CustomerBasicInfo(
                    name=user.username,
                    age=None,
                    gender=None,
                    phone=user.phone
                ),
                medical_history=profile.medical_history,
                allergies=profile.allergies,
                preferences=profile.preferences,
                tags=profile.tags.split(',') if profile.tags else None,
                risk_notes=profile.risk_notes if profile.risk_notes else None,
                created_at=profile.created_at,
                updated_at=profile.updated_at
            )
            customer_info.profile = profile_info
        
        return customer_info
    
    def create_customer(self, user_id: str, medical_history: Optional[str] = None,
                       allergies: Optional[str] = None, preferences: Optional[str] = None) -> Customer:
        """创建客户记录"""
        # 检查是否已存在
        existing_customer = self.db.query(Customer).filter(
            Customer.user_id == user_id
        ).first()
        
        if existing_customer:
            raise BusinessException("客户记录已存在", code=ErrorCode.RESOURCE_ALREADY_EXISTS)
        
        # 验证用户存在
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise BusinessException("用户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 创建客户记录
        customer = Customer(
            user_id=user_id,
            medical_history=medical_history,
            allergies=allergies,
            preferences=preferences
        )
        
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        
        return customer
    
    def update_customer(self, customer_id: str, medical_history: Optional[str] = None,
                       allergies: Optional[str] = None, preferences: Optional[str] = None) -> Customer:
        """更新客户信息"""
        customer = self.db.query(Customer).filter(
            Customer.user_id == customer_id
        ).first()
        
        if not customer:
            raise BusinessException("客户记录不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 更新字段
        if medical_history is not None:
            customer.medical_history = medical_history
        if allergies is not None:
            customer.allergies = allergies
        if preferences is not None:
            customer.preferences = preferences
        
        self.db.commit()
        self.db.refresh(customer)
        
        return customer
    
    # ============ 客户档案管理 ============
    
    def get_customer_profile(self, customer_id: str) -> Optional[CustomerProfileInfo]:
        """获取客户档案"""
        profile = self.db.query(CustomerProfile).filter(
            CustomerProfile.customer_id == customer_id
        ).first()
        
        if not profile:
            return None
        
        # 获取用户信息以构建完整的profile_info
        user = self.db.query(User).filter(User.id == customer_id).first()
        if not user:
            return None
        
        from app.customer.schemas.customer import CustomerBasicInfo
        profile_info = CustomerProfileInfo(
            id=profile.id,
            basicInfo=CustomerBasicInfo(
                name=user.username,
                age=None,
                gender=None,
                phone=user.phone
            ),
            medical_history=profile.medical_history,
            allergies=profile.allergies,
            preferences=profile.preferences,
            tags=profile.tags.split(',') if profile.tags else None,
            risk_notes=profile.risk_notes if profile.risk_notes else None,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
        
        return profile_info
    
    def create_customer_profile(self, customer_id: str, profile_data: CustomerProfileCreate) -> CustomerProfileInfo:
        """创建客户档案"""
        # 检查客户是否存在
        customer = self.db.query(Customer).filter(
            Customer.user_id == customer_id
        ).first()
        
        if not customer:
            raise BusinessException("客户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 检查档案是否已存在
        existing_profile = self.db.query(CustomerProfile).filter(
            CustomerProfile.customer_id == customer_id
        ).first()
        
        if existing_profile:
            raise BusinessException("客户档案已存在", code=ErrorCode.RESOURCE_ALREADY_EXISTS)
        
        # 创建档案
        profile_dict = profile_data.model_dump(exclude_unset=True)
        profile = CustomerProfile(
            customer_id=customer_id,
            medical_history=profile_dict.get('medical_history'),
            allergies=profile_dict.get('allergies'),
            preferences=profile_dict.get('preferences'),
            tags=profile_dict.get('tags'),
            risk_notes=profile_dict.get('risk_notes', [])
        )
        
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        
        # 获取用户信息以构建完整的profile_info
        user = self.db.query(User).filter(User.id == customer_id).first()
        if not user:
            raise BusinessException("用户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        from app.customer.schemas.customer import CustomerBasicInfo
        profile_info = CustomerProfileInfo(
            id=profile.id,
            basicInfo=CustomerBasicInfo(
                name=user.username,
                age=None,
                gender=None,
                phone=user.phone
            ),
            medical_history=profile.medical_history,
            allergies=profile.allergies,
            preferences=profile.preferences,
            tags=profile.tags.split(',') if profile.tags else None,
            risk_notes=profile.risk_notes if profile.risk_notes else None,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
        
        return profile_info
    
    def update_customer_profile(self, customer_id: str, profile_data: CustomerProfileUpdate) -> CustomerProfileInfo:
        """更新客户档案"""
        profile = self.db.query(CustomerProfile).filter(
            CustomerProfile.customer_id == customer_id
        ).first()
        
        if not profile:
            raise BusinessException("客户档案不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 更新字段
        update_dict = profile_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(profile, field, value)
        
        self.db.commit()
        self.db.refresh(profile)
        
        # 获取用户信息以构建完整的profile_info
        user = self.db.query(User).filter(User.id == customer_id).first()
        if not user:
            raise BusinessException("用户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        from app.customer.schemas.customer import CustomerBasicInfo
        profile_info = CustomerProfileInfo(
            id=profile.id,
            basicInfo=CustomerBasicInfo(
                name=user.username,
                age=None,
                gender=None,
                phone=user.phone
            ),
            medical_history=profile.medical_history,
            allergies=profile.allergies,
            preferences=profile.preferences,
            tags=profile.tags.split(',') if profile.tags else None,
            risk_notes=profile.risk_notes if profile.risk_notes else None,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
        
        return profile_info
    
    def delete_customer_profile(self, customer_id: str) -> bool:
        """删除客户档案"""
        profile = self.db.query(CustomerProfile).filter(
            CustomerProfile.customer_id == customer_id
        ).first()
        
        if not profile:
            return False
        
        self.db.delete(profile)
        self.db.commit()
        
        return True

