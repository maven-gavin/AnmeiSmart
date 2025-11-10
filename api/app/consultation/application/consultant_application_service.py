"""
顾问应用服务
负责顾问相关的用例编排和事务管理
"""
from typing import Optional, Dict, Any
import logging

from ..schemas.consultation import (
    ConsultantCreate,
    ConsultantResponse,
    ConsultantUpdate,
    ConsultantListResponse
)
from ..domain.entities.consultant import ConsultantEntity
from ..domain.consultant_domain_service import ConsultantDomainService
from ..infrastructure.repositories.consultant_repository import ConsultantRepository
from ..converters.consultant_converter import ConsultantConverter

logger = logging.getLogger(__name__)


class ConsultantApplicationService:
    """顾问应用服务 - 编排顾问相关的用例"""
    
    def __init__(
        self,
        consultant_repository: ConsultantRepository,
        consultant_domain_service: ConsultantDomainService
    ):
        self.consultant_repository = consultant_repository
        self.consultant_domain_service = consultant_domain_service
    
    async def create_consultant_use_case(self, request: ConsultantCreate) -> ConsultantResponse:
        """创建顾问用例"""
        try:
            # 转换请求数据
            consultant_data = ConsultantConverter.from_create_request(request)
            
            # 创建顾问实体
            consultant = ConsultantEntity.create(**consultant_data)
            
            # 保存到仓储
            saved_consultant = await self.consultant_repository.save(consultant)
            
            # 转换为响应格式
            return ConsultantConverter.to_response(saved_consultant)
            
        except ValueError as e:
            logger.error(f"创建顾问失败: {e}")
            raise
        except Exception as e:
            logger.error(f"创建顾问时发生系统错误: {e}")
            raise
    
    async def get_consultant_use_case(self, consultant_id: str) -> Optional[ConsultantResponse]:
        """获取顾问用例"""
        try:
            consultant = await self.consultant_repository.get_by_id(consultant_id)
            
            if not consultant:
                return None
            
            return ConsultantConverter.to_response(consultant)
            
        except Exception as e:
            logger.error(f"获取顾问失败: {e}")
            raise
    
    async def update_consultant_use_case(
        self,
        consultant_id: str,
        request: ConsultantUpdate
    ) -> Optional[ConsultantResponse]:
        """更新顾问用例"""
        try:
            # 获取现有顾问
            consultant = await self.consultant_repository.get_by_id(consultant_id)
            
            if not consultant:
                return None
            
            # 转换更新数据
            update_data = ConsultantConverter.from_update_request(request)
            
            # 更新顾问
            consultant.update_profile(**update_data)
            
            # 保存更新
            updated_consultant = await self.consultant_repository.save(consultant)
            
            return ConsultantConverter.to_response(updated_consultant)
            
        except ValueError as e:
            logger.error(f"更新顾问失败: {e}")
            raise
        except Exception as e:
            logger.error(f"更新顾问时发生系统错误: {e}")
            raise
    
    async def activate_consultant_use_case(self, consultant_id: str) -> Optional[ConsultantResponse]:
        """激活顾问用例"""
        try:
            consultant = await self.consultant_repository.get_by_id(consultant_id)
            
            if not consultant:
                return None
            
            consultant.activate()
            updated_consultant = await self.consultant_repository.save(consultant)
            
            return ConsultantConverter.to_response(updated_consultant)
            
        except ValueError as e:
            logger.error(f"激活顾问失败: {e}")
            raise
        except Exception as e:
            logger.error(f"激活顾问时发生系统错误: {e}")
            raise
    
    async def deactivate_consultant_use_case(self, consultant_id: str) -> Optional[ConsultantResponse]:
        """停用顾问用例"""
        try:
            consultant = await self.consultant_repository.get_by_id(consultant_id)
            
            if not consultant:
                return None
            
            consultant.deactivate()
            updated_consultant = await self.consultant_repository.save(consultant)
            
            return ConsultantConverter.to_response(updated_consultant)
            
        except ValueError as e:
            logger.error(f"停用顾问失败: {e}")
            raise
        except Exception as e:
            logger.error(f"停用顾问时发生系统错误: {e}")
            raise
    
    async def list_consultants_use_case(
        self,
        specialization: Optional[str] = None,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> ConsultantListResponse:
        """查询顾问列表用例"""
        try:
            # 构建查询条件
            filters = {}
            if specialization:
                filters["specialization"] = specialization
            if is_active is not None:
                filters["is_active"] = is_active
            
            # 查询顾问列表
            consultants = await self.consultant_repository.find_by_filters(
                filters=filters,
                skip=skip,
                limit=limit
            )
            
            return ConsultantConverter.to_list_response(consultants)
            
        except Exception as e:
            logger.error(f"查询顾问列表失败: {e}")
            raise
    
    async def get_consultant_workload_use_case(self, consultant_id: str) -> Optional[Dict[str, Any]]:
        """获取顾问工作负载用例"""
        try:
            consultant = await self.consultant_repository.get_by_id(consultant_id)
            
            if not consultant:
                return None
            
            return self.consultant_domain_service.get_consultant_workload(consultant)
            
        except Exception as e:
            logger.error(f"获取顾问工作负载失败: {e}")
            raise
