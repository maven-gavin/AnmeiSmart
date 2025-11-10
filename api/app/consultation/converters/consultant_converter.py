"""
顾问数据转换器
"""
from typing import List, Dict, Any

from ..schemas.consultation import (
    ConsultantCreate,
    ConsultantResponse,
    ConsultantUpdate,
    ConsultantListResponse
)
from ..domain.entities.consultant import ConsultantEntity


class ConsultantConverter:
    """顾问数据转换器"""
    
    @staticmethod
    def to_response(consultant: ConsultantEntity) -> ConsultantResponse:
        """转换顾问实体为响应格式"""
        return ConsultantResponse(
            id=consultant.id,
            user_id=consultant.userId,
            name=consultant.name,
            specialization=consultant.specialization,
            experience_years=consultant.experienceYears,
            is_active=consultant.isActive,
            created_at=consultant.createdAt,
            updated_at=consultant.updatedAt,
            metadata=dict(consultant.metadata)
        )
    
    @staticmethod
    def to_list_response(consultants: List[ConsultantEntity]) -> ConsultantListResponse:
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
            "userId": request.user_id,
            "name": request.name,
            "specialization": request.specialization,
            "experienceYears": request.experience_years,
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
            update_data["experienceYears"] = request.experience_years
        
        if request.metadata is not None:
            update_data["metadata"] = request.metadata
        
        return update_data
    
    @staticmethod
    def from_model(model) -> ConsultantEntity:
        """从ORM模型转换为领域实体"""
        return ConsultantEntity(
            id=model.id,
            userId=model.user_id,
            name=model.name,
            specialization=model.specialization,
            experienceYears=model.experience_years,
            isActive=model.is_active,
            createdAt=model.created_at,
            updatedAt=model.updated_at,
            _metadata=model.metadata or {}
        )
    
    @staticmethod
    def to_model_dict(consultant: ConsultantEntity) -> Dict[str, Any]:
        """转换领域实体为ORM模型字典"""
        return {
            "id": consultant.id,
            "user_id": consultant.userId,
            "name": consultant.name,
            "specialization": consultant.specialization,
            "experience_years": consultant.experienceYears,
            "is_active": consultant.isActive,
            "created_at": consultant.createdAt,
            "updated_at": consultant.updatedAt,
            "metadata": dict(consultant.metadata)
        }
