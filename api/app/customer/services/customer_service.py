"""
客户服务 - 核心业务逻辑
处理客户CRUD、客户档案管理等功能
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc

from app.customer.models.customer import Customer, CustomerProfile, CustomerInsight, InsightStatus
from app.customer.schemas.customer import (
    CustomerInfo,
    CustomerProfileInfo,
    CustomerProfileCreate,
    CustomerProfileUpdate,
    CustomerInsightCreate,
    CustomerInsightInfo,
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
            
            # 获取客户档案信息 (用于列表展示关键状态)
            profile = self.db.query(CustomerProfile).filter(
                CustomerProfile.customer_id == customer_user.id
            ).first()
            
            life_cycle_stage = profile.life_cycle_stage if profile else 'lead'
            
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
                "life_cycle_stage": life_cycle_stage,
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
            # 如果没有客户记录，自动创建最小 Customer 记录
            customer = Customer(user_id=customer_id)
            self.db.add(customer)
            self.db.commit()
            self.db.refresh(customer)
        
        # 获取客户档案
        profile = self.get_customer_profile(customer_id)
        
        # 构建响应
        customer_dict = {
            "id": user.id,
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "phone": user.phone,
            "avatar": user.avatar,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "profile": profile
        }
        
        return CustomerInfo(**customer_dict)
    
    def create_customer(self, user_id: str) -> Customer:
        """创建客户记录 (简化版，不再包含详细病史等)"""
        # 检查是否已存在
        existing_customer = self.db.query(Customer).filter(
            Customer.user_id == user_id
        ).first()
        
        if existing_customer:
            return existing_customer
        
        # 验证用户存在
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise BusinessException("用户不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        # 创建客户记录
        customer = Customer(user_id=user_id)
        
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        
        # 同时自动创建空档案
        self.create_customer_profile(user_id, CustomerProfileCreate())
        
        return customer
    
    def update_customer(self, customer_id: str) -> Customer:
        """更新客户信息 (目前仅保留接口，实际业务逻辑已移至档案更新)"""
        customer = self.db.query(Customer).filter(
            Customer.user_id == customer_id
        ).first()
        
        if not customer:
            raise BusinessException("客户记录不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        return customer
    
    # ============ 客户档案管理 ============
    
    def get_customer_profile(self, customer_id: str) -> Optional[CustomerProfileInfo]:
        """获取客户档案（包含Active的洞察）"""
        profile = self.db.query(CustomerProfile).filter(
            CustomerProfile.customer_id == customer_id
        ).first()
        
        if not profile:
            return None
        
        # 获取用户信息
        user = self.db.query(User).filter(User.id == customer_id).first()
        if not user:
            return None
        
        # 获取 Active Insights
        active_insights = self.db.query(CustomerInsight).filter(
            CustomerInsight.profile_id == profile.id,
            CustomerInsight.status == InsightStatus.ACTIVE
        ).order_by(desc(CustomerInsight.created_at)).all()
        
        insight_infos = [CustomerInsightInfo.model_validate(insight) for insight in active_insights]
        
        profile_info = CustomerProfileInfo(
            id=profile.id,
            customer_id=customer_id,
            life_cycle_stage=profile.life_cycle_stage,
            industry=profile.industry,
            company_scale=profile.company_scale,
            ai_summary=profile.ai_summary,
            extra_data=profile.extra_data,
            active_insights=insight_infos,
            created_at=profile.created_at,
            updated_at=profile.updated_at
        )
        
        return profile_info
    
    def create_customer_profile(self, customer_id: str, profile_data: CustomerProfileCreate) -> CustomerProfileInfo:
        """创建客户档案"""
        existing_profile = self.db.query(CustomerProfile).filter(
            CustomerProfile.customer_id == customer_id
        ).first()
        
        if existing_profile:
            return self.get_customer_profile(customer_id)
        
        profile_dict = profile_data.model_dump(exclude_unset=True)
        profile = CustomerProfile(
            customer_id=customer_id,
            **profile_dict
        )
        
        self.db.add(profile)
        self.db.commit()
        self.db.refresh(profile)
        
        return self.get_customer_profile(customer_id)
    
    def update_customer_profile(self, customer_id: str, profile_data: CustomerProfileUpdate) -> CustomerProfileInfo:
        """更新客户档案核心信息"""
        profile = self.db.query(CustomerProfile).filter(
            CustomerProfile.customer_id == customer_id
        ).first()
        
        if not profile:
            raise BusinessException("客户档案不存在", code=ErrorCode.RESOURCE_NOT_FOUND)
        
        update_dict = profile_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(profile, field, value)
        
        self.db.commit()
        self.db.refresh(profile)
        
        return self.get_customer_profile(customer_id)

    # ============ 洞察/画像管理 (Insights) ============
    
    def add_insight(self, insight_data: CustomerInsightCreate) -> CustomerInsightInfo:
        """添加一条新的洞察"""
        # 1. 验证 Profile
        profile = self.db.query(CustomerProfile).filter(
            CustomerProfile.id == insight_data.profile_id
        ).first()
        if not profile:
             raise BusinessException("客户档案不存在", code=ErrorCode.RESOURCE_NOT_FOUND)

        # 2. 自动归档“单值类维度”的旧洞察（状态管理默认开启）
        single_value_categories = {
            "budget",
            "authority",
            "timeline",
        }
        if insight_data.category in single_value_categories:
            self.db.query(CustomerInsight).filter(
                CustomerInsight.profile_id == insight_data.profile_id,
                CustomerInsight.category == insight_data.category,
                CustomerInsight.status == InsightStatus.ACTIVE,
            ).update({"status": InsightStatus.ARCHIVED}, synchronize_session=False)
        
        insight = CustomerInsight(
            profile_id=insight_data.profile_id,
            category=insight_data.category,
            content=insight_data.content,
            source=insight_data.source,
            created_by_name=insight_data.created_by_name,
            confidence=insight_data.confidence,
            status=InsightStatus.ACTIVE
        )
        
        self.db.add(insight)
        self.db.commit()
        self.db.refresh(insight)
        
        return CustomerInsightInfo.model_validate(insight)

    def archive_insight(self, insight_id: str) -> bool:
        """归档一条洞察"""
        insight = self.db.query(CustomerInsight).filter(CustomerInsight.id == insight_id).first()
        if not insight:
            return False
            
        insight.status = InsightStatus.ARCHIVED
        self.db.commit()
        return True
