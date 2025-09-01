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
from ..domain.entities.consultation import Consultation
from ..domain.value_objects.consultation_status import ConsultationStatus


class ConsultationConverter:
    """咨询数据转换器"""
    
    @staticmethod
    def to_response(consultation: Consultation) -> ConsultationResponse:
        """转换咨询实体为响应格式"""
        return ConsultationResponse(
            id=consultation.id,
            customer_id=consultation.customer_id,
            consultant_id=consultation.consultant_id,
            status=consultation.status.value,
            title=consultation.title,
            created_at=consultation.created_at,
            updated_at=consultation.updated_at,
            metadata=consultation.metadata
        )
    
    @staticmethod
    def to_list_response(consultations: List[Consultation]) -> ConsultationListResponse:
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
            "customer_id": request.customer_id,
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
    def from_model(model) -> Consultation:
        """从ORM模型转换为领域实体"""
        return Consultation(
            id=model.id,
            customer_id=model.customer_id,
            consultant_id=model.consultant_id,
            status=ConsultationStatus.from_string(model.status),
            title=model.title,
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata=model.metadata or {}
        )
    
    @staticmethod
    def to_model_dict(consultation: Consultation) -> Dict[str, Any]:
        """转换领域实体为ORM模型字典"""
        return {
            "id": consultation.id,
            "customer_id": consultation.customer_id,
            "consultant_id": consultation.consultant_id,
            "status": consultation.status.value,
            "title": consultation.title,
            "created_at": consultation.created_at,
            "updated_at": consultation.updated_at,
            "metadata": consultation.metadata
        }
