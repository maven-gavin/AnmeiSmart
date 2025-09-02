"""
客户应用服务 - 编排领域逻辑，实现用例
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.customer.domain.entities.customer import Customer, CustomerProfile
from app.customer.domain.customer_domain_service import CustomerDomainService
from app.customer.infrastructure.repositories.customer_repository import CustomerRepository
from app.customer.infrastructure.repositories.customer_profile_repository import CustomerProfileRepository
from app.customer.converters.customer_converter import CustomerConverter
from app.customer.converters.customer_profile_converter import CustomerProfileConverter
from app.customer.schemas.customer import CustomerInfo, CustomerProfileInfo, CustomerProfileCreate, CustomerProfileUpdate
from app.identity_access.infrastructure.db.user import User

logger = logging.getLogger(__name__)


class CustomerApplicationService:
    """客户应用服务 - 统一处理客户相关功能"""
    
    def __init__(
        self,
        customer_repository: CustomerRepository,
        customer_profile_repository: CustomerProfileRepository,
        customer_domain_service: CustomerDomainService
    ):
        self.customer_repository = customer_repository
        self.customer_profile_repository = customer_profile_repository
        self.customer_domain_service = customer_domain_service
    
    # 客户管理用例
    
    async def get_customers_use_case(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """获取客户列表用例"""
        try:
            customers_data = await self.customer_repository.get_customers_with_users(skip, limit)
            return customers_data
        except Exception as e:
            logger.error(f"获取客户列表失败: {e}")
            raise
    
    async def get_customer_use_case(self, customer_id: str) -> CustomerInfo:
        """获取客户详细信息用例"""
        try:
            # 获取客户信息
            customer = await self.customer_repository.get_by_user_id(customer_id)
            if not customer:
                raise ValueError("客户不存在")
            
            # 获取用户信息
            from app.identity_access.infrastructure.db.user import User
            user = self.customer_repository.db.query(User).filter(User.id == customer_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            # 获取客户档案
            profile = await self.customer_profile_repository.get_by_customer_id(customer_id)
            
            # 构建响应
            result = CustomerConverter.to_response(customer, user)
            
            if profile:
                # 获取用户信息以构建profile响应
                result.profile = CustomerProfileConverter.to_response(profile, user)
            
            return result
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"获取客户信息失败: {e}")
            raise
    
    async def create_customer_use_case(
        self,
        user_id: str,
        customer_data: Dict[str, Any]
    ) -> CustomerInfo:
        """创建客户用例"""
        try:
            # 领域逻辑验证
            self.customer_domain_service.validate_customer_data(
                medical_history=customer_data.get('medical_history'),
                allergies=customer_data.get('allergies'),
                preferences=customer_data.get('preferences')
            )
            
            # 检查是否已存在
            if await self.customer_repository.exists_by_user_id(user_id):
                raise ValueError("客户信息已存在")
            
            # 创建领域对象
            customer = Customer.create(
                user_id=user_id,
                medical_history=customer_data.get('medical_history'),
                allergies=customer_data.get('allergies'),
                preferences=customer_data.get('preferences')
            )
            
            # 持久化
            saved_customer = await self.customer_repository.save(customer)
            
            # 获取用户信息
            user = self.customer_repository.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            return CustomerConverter.to_response(saved_customer, user)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"创建客户失败: {e}")
            raise
    
    async def update_customer_use_case(
        self,
        user_id: str,
        update_data: Dict[str, Any]
    ) -> CustomerInfo:
        """更新客户信息用例"""
        try:
            # 获取现有客户
            customer = await self.customer_repository.get_by_user_id(user_id)
            if not customer:
                raise ValueError("客户不存在")
            
            # 领域逻辑验证
            self.customer_domain_service.validate_customer_data(
                medical_history=update_data.get('medical_history'),
                allergies=update_data.get('allergies'),
                preferences=update_data.get('preferences')
            )
            
            # 更新客户信息
            if 'medical_history' in update_data:
                customer.update_medical_history(update_data['medical_history'])
            
            if 'allergies' in update_data:
                customer.update_allergies(update_data['allergies'])
            
            if 'preferences' in update_data:
                customer.update_preferences(update_data['preferences'])
            
            # 持久化
            updated_customer = await self.customer_repository.save(customer)
            
            # 获取用户信息
            user = self.customer_repository.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            return CustomerConverter.to_response(updated_customer, user)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"更新客户信息失败: {e}")
            raise
    
    # 客户档案管理用例
    
    async def get_customer_profile_use_case(self, customer_id: str) -> CustomerProfileInfo:
        """获取客户档案用例"""
        try:
            # 获取客户档案
            profile = await self.customer_profile_repository.get_by_customer_id(customer_id)
            if not profile:
                raise ValueError("客户档案不存在")
            
            # 获取用户信息
            user = self.customer_profile_repository.db.query(User).filter(User.id == customer_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            return CustomerProfileConverter.to_response(profile, user)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"获取客户档案失败: {e}")
            raise
    
    async def create_customer_profile_use_case(
        self,
        customer_id: str,
        profile_data: CustomerProfileCreate
    ) -> CustomerProfileInfo:
        """创建客户档案用例"""
        try:
            # 检查客户是否存在
            customer = await self.customer_repository.get_by_user_id(customer_id)
            if not customer:
                raise ValueError("客户不存在")
            
            # 检查是否已存在档案
            if await self.customer_profile_repository.exists_by_customer_id(customer_id):
                raise ValueError("客户档案已存在")
            
            # 领域逻辑验证
            self.customer_domain_service.validate_profile_data(
                medical_history=profile_data.medical_history,
                allergies=profile_data.allergies,
                preferences=profile_data.preferences,
                tags=profile_data.tags
            )
            
            # 创建领域对象
            profile = CustomerProfile.create(
                customer_id=customer_id,
                medical_history=profile_data.medical_history,
                allergies=profile_data.allergies,
                preferences=profile_data.preferences,
                tags=profile_data.tags
            )
            
            # 持久化
            saved_profile = await self.customer_profile_repository.save(profile)
            
            # 获取用户信息
            user = self.customer_profile_repository.db.query(User).filter(User.id == customer_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            return CustomerProfileConverter.to_response(saved_profile, user)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"创建客户档案失败: {e}")
            raise
    
    async def update_customer_profile_use_case(
        self,
        customer_id: str,
        profile_data: CustomerProfileUpdate
    ) -> CustomerProfileInfo:
        """更新客户档案用例"""
        try:
            # 获取现有档案
            profile = await self.customer_profile_repository.get_by_customer_id(customer_id)
            if not profile:
                raise ValueError("客户档案不存在")
            
            # 领域逻辑验证
            if profile_data.medical_history is not None:
                self.customer_domain_service.validate_profile_data(
                    medical_history=profile_data.medical_history
                )
            
            if profile_data.allergies is not None:
                self.customer_domain_service.validate_profile_data(
                    allergies=profile_data.allergies
                )
            
            if profile_data.preferences is not None:
                self.customer_domain_service.validate_profile_data(
                    preferences=profile_data.preferences
                )
            
            if profile_data.tags is not None:
                self.customer_domain_service.validate_profile_data(
                    tags=profile_data.tags
                )
            
            # 验证风险提示
            if profile_data.risk_notes:
                for risk_note in profile_data.risk_notes:
                    self.customer_domain_service.validate_risk_note(risk_note.model_dump())
            
            # 更新档案信息
            if profile_data.medical_history is not None:
                profile.update_medical_history(profile_data.medical_history)
            
            if profile_data.allergies is not None:
                profile.update_allergies(profile_data.allergies)
            
            if profile_data.preferences is not None:
                profile.update_preferences(profile_data.preferences)
            
            if profile_data.tags is not None:
                profile.update_tags(profile_data.tags)
            
            if profile_data.risk_notes is not None:
                profile.risk_notes = [note.model_dump() for note in profile_data.risk_notes]
                profile.updated_at = datetime.now()
            
            # 持久化
            updated_profile = await self.customer_profile_repository.save(profile)
            
            # 获取用户信息
            user = self.customer_profile_repository.db.query(User).filter(User.id == customer_id).first()
            if not user:
                raise ValueError("用户不存在")
            
            return CustomerProfileConverter.to_response(updated_profile, user)
            
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"更新客户档案失败: {e}")
            raise
    
    # 辅助方法
    
    def get_user_role(self, user: User) -> str:
        """获取用户的当前角色"""
        if hasattr(user, '_active_role') and user._active_role:
            return user._active_role
        elif user.roles:
            return user.roles[0].name
        else:
            return 'customer'  # 默认角色
    
    def check_permission(self, user: User, required_roles: List[str]) -> bool:
        """检查用户权限"""
        user_role = self.get_user_role(user)
        return user_role in required_roles
