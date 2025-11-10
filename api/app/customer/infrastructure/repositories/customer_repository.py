"""
客户仓储实现
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload

from app.customer.domain.entities.customer import CustomerEntity
from app.customer.infrastructure.db.customer import Customer as CustomerModel


class CustomerRepository:
    """客户仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def save(self, customer: CustomerEntity) -> CustomerEntity:
        """保存客户信息"""
        # 检查是否已存在
        existing_customer = self.db.query(CustomerModel).filter(
            CustomerModel.user_id == customer.userId
        ).first()
        
        if existing_customer:
            # 更新现有记录
            existing_customer.medical_history = customer.medicalHistory
            existing_customer.allergies = customer.allergies
            existing_customer.preferences = customer.preferences
            existing_customer.updated_at = customer.updatedAt
            customer_to_save = existing_customer
        else:
            # 创建新记录
            customer_to_save = CustomerModel(
                id=customer.id,
                user_id=customer.userId,
                medical_history=customer.medicalHistory,
                allergies=customer.allergies,
                preferences=customer.preferences,
                created_at=customer.createdAt,
                updated_at=customer.updatedAt
            )
            self.db.add(customer_to_save)
        
        self.db.commit()
        self.db.refresh(customer_to_save)
        
        return self._to_entity(customer_to_save)
    
    async def get_by_id(self, customer_id: str) -> Optional[CustomerEntity]:
        """根据ID获取客户"""
        customer_model = self.db.query(CustomerModel).filter(
            CustomerModel.id == customer_id
        ).first()
        
        if not customer_model:
            return None
        
        return self._to_entity(customer_model)
    
    async def get_by_user_id(self, user_id: str) -> Optional[CustomerEntity]:
        """根据用户ID获取客户"""
        customer_model = self.db.query(CustomerModel).filter(
            CustomerModel.user_id == user_id
        ).first()
        
        if not customer_model:
            return None
        
        return self._to_entity(customer_model)
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[CustomerEntity]:
        """获取所有客户"""
        customers = self.db.query(CustomerModel).offset(skip).limit(limit).all()
        return [self._to_entity(customer) for customer in customers]
    
    async def get_customers_with_users(self, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """获取客户列表，包含用户信息和聊天统计"""
        # 延迟导入避免循环依赖
        from app.identity_access.infrastructure.db.user import User
        
        # 查询客户用户
        customers_query = self.db.query(User).join(User.roles).filter(
            User.is_active == True
        )
        
        customers = customers_query.offset(skip).limit(limit).all()
        
        # 导入聊天相关模型
        from app.chat.infrastructure.db.chat import Message, Conversation
        
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
            customer_info = self.db.query(CustomerModel).filter(
                CustomerModel.user_id == customer_user.id
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
    
    async def exists_by_user_id(self, user_id: str) -> bool:
        """检查用户ID是否存在客户记录"""
        return self.db.query(CustomerModel).filter(
            CustomerModel.user_id == user_id
        ).first() is not None
    
    async def delete_by_user_id(self, user_id: str) -> bool:
        """根据用户ID删除客户记录"""
        customer = self.db.query(CustomerModel).filter(
            CustomerModel.user_id == user_id
        ).first()
        
        if customer:
            self.db.delete(customer)
            self.db.commit()
            return True
        
        return False
    
    def _to_entity(self, model: CustomerModel) -> CustomerEntity:
        """ORM模型转换为领域实体"""
        from app.customer.domain.entities.customer import CustomerEntity
        
        return CustomerEntity(
            id=model.id,
            userId=model.user_id,
            medicalHistory=model.medical_history,
            allergies=model.allergies,
            preferences=model.preferences,
            createdAt=model.created_at,
            updatedAt=model.updated_at
        )
    
    def _to_model(self, entity: CustomerEntity) -> CustomerModel:
        """领域实体转换为ORM模型"""
        return CustomerModel(
            id=entity.id,
            user_id=entity.userId,
            medical_history=entity.medicalHistory,
            allergies=entity.allergies,
            preferences=entity.preferences,
            created_at=entity.createdAt,
            updated_at=entity.updatedAt
        )
