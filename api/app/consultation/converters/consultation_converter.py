"""
咨询数据转换器
"""
from typing import List, Dict, Any

from ..schemas.consultation import (
    ConsultationCreate,
    ConsultationResponse,
    ConsultationUpdate,
    ConsultationListResponse
)
from ..domain.entities.consultation import ConsultationEntity
from ..domain.value_objects.consultation_status import ConsultationStatus


class ConsultationConverter:
    """咨询数据转换器"""
    
    @staticmethod
    def to_response(consultation: ConsultationEntity) -> ConsultationResponse:
        """转换咨询实体为响应格式"""
        return ConsultationResponse(
            id=consultation.id,
            customer_id=consultation.customerId,
            consultant_id=consultation.consultantId,
            status=consultation.status.value,
            title=consultation.title,
            created_at=consultation.createdAt,
            updated_at=consultation.updatedAt,
            metadata=dict(consultation.metadata)
        )
    
    @staticmethod
    def to_list_response(consultations: List[ConsultationEntity]) -> ConsultationListResponse:
        """转换咨询列表为响应格式"""
        consultation_responses = [
            ConsultationConverter.to_response(consultation) 
            for consultation in consultations
        ]
        
        return ConsultationListResponse(
            consultations=consultation_responses,
            total=len(consultation_responses)
        )
    
    @staticmethod
    def from_create_request(request: ConsultationCreate) -> Dict[str, Any]:
        """从创建请求转换为领域对象参数"""
        return {
            "customerId": request.customer_id,
            "title": request.title,
            "metadata": request.metadata or {}
        }
    
    @staticmethod
    def from_update_request(request: ConsultationUpdate) -> Dict[str, Any]:
        """从更新请求转换为领域对象参数"""
        update_data = {}
        
        if request.title is not None:
            update_data["title"] = request.title
        
        if request.metadata is not None:
            update_data["metadata"] = request.metadata
        
        return update_data
    
    @staticmethod
    def from_model(model) -> ConsultationEntity:
        """从ORM模型转换为领域实体"""
        return ConsultationEntity(
            id=model.id,
            customerId=model.customer_id,
            consultantId=model.consultant_id,
            status=ConsultationStatus.from_string(model.status),
            title=model.title,
            createdAt=model.created_at,
            updatedAt=model.updated_at,
            _metadata=model.metadata or {}
        )
    
    @staticmethod
    def to_model_dict(consultation: ConsultationEntity) -> Dict[str, Any]:
        """转换领域实体为ORM模型字典"""
        return {
            "id": consultation.id,
            "customer_id": consultation.customerId,
            "consultant_id": consultation.consultantId,
            "status": consultation.status.value,
            "title": consultation.title,
            "created_at": consultation.createdAt,
            "updated_at": consultation.updatedAt,
            "metadata": dict(consultation.metadata)
        }
