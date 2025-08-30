"""
顾问数据转换器
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.schemas.consultation import (
    ConsultantCreate,
    ConsultantResponse,
    ConsultantUpdate,
    ConsultantListResponse
)
from ..domain.entities.consultant import Consultant


class ConsultantConverter:
    """顾问数据转换器"""
    
    @staticmethod
    def to_response(consultant: Consultant) -> ConsultantResponse:
        """转换顾问实体为响应格式"""
        return ConsultantResponse(
            id=consultant.id,
            user_id=consultant.user_id,
            name=consultant.name,
            specialization=consultant.specialization,
            experience_years=consultant.experience_years,
            is_active=consultant.is_active,
            created_at=consultant.created_at,
            updated_at=consultant.updated_at,
            metadata=consultant.metadata
        )
    
    @staticmethod
    def to_list_response(consultants: List[Consultant]) -> ConsultantListResponse:
        """转换顾问列表为响应格式"""
        consultant_responses = [
            ConsultantConverter.to_response(consultant) 
            for consultant in consultants
        ]
        
        return ConsultantListResponse(
            consultants=consultant_responses,
            total=len(consultant_responses)
        )
    
    @staticmethod
    def from_create_request(request: ConsultantCreate) -> Dict[str, Any]:
        """从创建请求转换为领域对象参数"""
        return {
            "user_id": request.user_id,
            "name": request.name,
            "specialization": request.specialization,
            "experience_years": request.experience_years,
            "metadata": request.metadata or {}
        }
    
    @staticmethod
    def from_update_request(request: ConsultantUpdate) -> Dict[str, Any]:
        """从更新请求转换为领域对象参数"""
        update_data = {}
        
        if request.name is not None:
            update_data["name"] = request.name
        
        if request.specialization is not None:
            update_data["specialization"] = request.specialization
        
        if request.experience_years is not None:
            update_data["experience_years"] = request.experience_years
        
        if request.metadata is not None:
            update_data["metadata"] = request.metadata
        
        return update_data
    
    @staticmethod
    def from_model(model) -> Consultant:
        """从ORM模型转换为领域实体"""
        return Consultant(
            id=model.id,
            user_id=model.user_id,
            name=model.name,
            specialization=model.specialization,
            experience_years=model.experience_years,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata=model.metadata or {}
        )
    
    @staticmethod
    def to_model_dict(consultant: Consultant) -> Dict[str, Any]:
        """转换领域实体为ORM模型字典"""
        return {
            "id": consultant.id,
            "user_id": consultant.user_id,
            "name": consultant.name,
            "specialization": consultant.specialization,
            "experience_years": consultant.experience_years,
            "is_active": consultant.is_active,
            "created_at": consultant.created_at,
            "updated_at": consultant.updated_at,
            "metadata": consultant.metadata
        }
