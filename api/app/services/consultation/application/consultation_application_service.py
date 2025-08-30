"""
咨询应用服务
负责咨询相关的用例编排和事务管理
遵循DDD分层架构，只处理咨询核心业务逻辑
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import logging

from app.schemas.consultation import (
    ConsultationCreate,
    ConsultationResponse,
    ConsultationUpdate,
    ConsultationListResponse
)
from ..domain.entities.consultation import Consultation
from ..domain.consultation_domain_service import ConsultationDomainService
from ..infrastructure.repositories.consultation_repository import ConsultationRepository
from ..converters.consultation_converter import ConsultationConverter

logger = logging.getLogger(__name__)


class ConsultationApplicationService:
    """咨询应用服务 - 编排咨询相关的用例"""
    
    def __init__(
        self,
        consultation_repository: ConsultationRepository,
        consultation_domain_service: ConsultationDomainService
    ):
        self.consultation_repository = consultation_repository
        self.consultation_domain_service = consultation_domain_service
    
    async def create_consultation_use_case(
        self,
        request: ConsultationCreate
    ) -> ConsultationResponse:
        """创建咨询用例"""
        try:
            # 转换请求数据
            consultation_data = ConsultationConverter.from_create_request(request)
            
            # 创建咨询实体
            consultation = Consultation.create(**consultation_data)
            
            # 保存到仓储
            saved_consultation = await self.consultation_repository.save(consultation)
            
            # 转换为响应格式
            return ConsultationConverter.to_response(saved_consultation)
            
        except ValueError as e:
            logger.error(f"创建咨询失败: {e}")
            raise
        except Exception as e:
            logger.error(f"创建咨询时发生系统错误: {e}")
            raise
    
    async def get_consultation_use_case(self, consultation_id: str) -> Optional[ConsultationResponse]:
        """获取咨询用例"""
        try:
            consultation = await self.consultation_repository.get_by_id(consultation_id)
            
            if not consultation:
                return None
            
            return ConsultationConverter.to_response(consultation)
            
        except Exception as e:
            logger.error(f"获取咨询失败: {e}")
            raise
    
    async def update_consultation_use_case(
        self,
        consultation_id: str,
        request: ConsultationUpdate
    ) -> Optional[ConsultationResponse]:
        """更新咨询用例"""
        try:
            # 获取现有咨询
            consultation = await self.consultation_repository.get_by_id(consultation_id)
            
            if not consultation:
                return None
            
            # 转换更新数据
            update_data = ConsultationConverter.from_update_request(request)
            
            # 更新咨询
            if "title" in update_data:
                consultation._title = update_data["title"]
            
            if "metadata" in update_data:
                consultation.update_metadata(update_data["metadata"])
            
            # 保存更新
            updated_consultation = await self.consultation_repository.save(consultation)
            
            return ConsultationConverter.to_response(updated_consultation)
            
        except ValueError as e:
            logger.error(f"更新咨询失败: {e}")
            raise
        except Exception as e:
            logger.error(f"更新咨询时发生系统错误: {e}")
            raise
    
    async def assign_consultant_use_case(
        self,
        consultation_id: str,
        consultant_id: str
    ) -> Optional[ConsultationResponse]:
        """分配顾问用例"""
        try:
            # 获取咨询
            consultation = await self.consultation_repository.get_by_id(consultation_id)
            
            if not consultation:
                return None
            
            # 分配顾问
            consultation.assign_consultant(consultant_id)
            
            # 保存更新
            updated_consultation = await self.consultation_repository.save(consultation)
            
            return ConsultationConverter.to_response(updated_consultation)
            
        except ValueError as e:
            logger.error(f"分配顾问失败: {e}")
            raise
        except Exception as e:
            logger.error(f"分配顾问时发生系统错误: {e}")
            raise
    
    async def complete_consultation_use_case(self, consultation_id: str) -> Optional[ConsultationResponse]:
        """完成咨询用例"""
        try:
            # 获取咨询
            consultation = await self.consultation_repository.get_by_id(consultation_id)
            
            if not consultation:
                return None
            
            # 完成咨询
            consultation.complete_consultation()
            
            # 保存更新
            updated_consultation = await self.consultation_repository.save(consultation)
            
            return ConsultationConverter.to_response(updated_consultation)
            
        except ValueError as e:
            logger.error(f"完成咨询失败: {e}")
            raise
        except Exception as e:
            logger.error(f"完成咨询时发生系统错误: {e}")
            raise
    
    async def cancel_consultation_use_case(
        self,
        consultation_id: str,
        reason: Optional[str] = None
    ) -> Optional[ConsultationResponse]:
        """取消咨询用例"""
        try:
            # 获取咨询
            consultation = await self.consultation_repository.get_by_id(consultation_id)
            
            if not consultation:
                return None
            
            # 取消咨询
            consultation.cancel_consultation(reason)
            
            # 保存更新
            updated_consultation = await self.consultation_repository.save(consultation)
            
            return ConsultationConverter.to_response(updated_consultation)
            
        except ValueError as e:
            logger.error(f"取消咨询失败: {e}")
            raise
        except Exception as e:
            logger.error(f"取消咨询时发生系统错误: {e}")
            raise
    
    async def list_consultations_use_case(
        self,
        customer_id: Optional[str] = None,
        consultant_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> ConsultationListResponse:
        """查询咨询列表用例"""
        try:
            # 构建查询条件
            filters = {}
            if customer_id:
                filters["customer_id"] = customer_id
            if consultant_id:
                filters["consultant_id"] = consultant_id
            if status:
                filters["status"] = status
            
            # 查询咨询列表
            consultations = await self.consultation_repository.find_by_filters(
                filters=filters,
                skip=skip,
                limit=limit
            )
            
            return ConsultationConverter.to_list_response(consultations)
            
        except Exception as e:
            logger.error(f"查询咨询列表失败: {e}")
            raise
