"""
方案数据转换器
"""
from typing import List, Dict, Any

from ..schemas.consultation import (
    PlanCreate,
    PlanResponse,
    PlanUpdate,
    PlanListResponse
)
from ..domain.entities.plan import PlanEntity
from ..domain.value_objects.plan_status import PlanStatus


class PlanConverter:
    """方案数据转换器"""
    
    @staticmethod
    def to_response(plan: PlanEntity) -> PlanResponse:
        """转换方案实体为响应格式"""
        return PlanResponse(
            id=plan.id,
            consultation_id=plan.consultationId,
            customer_id=plan.customerId,
            consultant_id=plan.consultantId,
            status=plan.status.value,
            title=plan.title,
            content=plan.content,
            version=plan.version,
            created_at=plan.createdAt,
            updated_at=plan.updatedAt,
            metadata=dict(plan.metadata)
        )
    
    @staticmethod
    def to_list_response(plans: List[PlanEntity]) -> PlanListResponse:
        """转换方案列表为响应格式"""
        plan_responses = [
            PlanConverter.to_response(plan) 
            for plan in plans
        ]
        
        return PlanListResponse(
            plans=plan_responses,
            total=len(plan_responses)
        )
    
    @staticmethod
    def from_create_request(request: PlanCreate) -> Dict[str, Any]:
        """从创建请求转换为领域对象参数"""
        return {
            "consultationId": request.consultation_id,
            "customerId": request.customer_id,
            "consultantId": request.consultant_id,
            "title": request.title,
            "content": request.content,
            "metadata": request.metadata or {}
        }
    
    @staticmethod
    def from_update_request(request: PlanUpdate) -> Dict[str, Any]:
        """从更新请求转换为领域对象参数"""
        update_data = {}
        
        if request.title is not None:
            update_data["title"] = request.title
        
        if request.content is not None:
            update_data["content"] = request.content
        
        if request.metadata is not None:
            update_data["metadata"] = request.metadata
        
        return update_data
    
    @staticmethod
    def from_model(model) -> PlanEntity:
        """从ORM模型转换为领域实体"""
        return PlanEntity(
            id=model.id,
            consultationId=model.consultation_id,
            customerId=model.customer_id,
            consultantId=model.consultant_id,
            status=PlanStatus.from_string(model.status),
            title=model.title,
            content=model.content,
            version=model.version,
            createdAt=model.created_at,
            updatedAt=model.updated_at,
            _metadata=model.metadata or {}
        )
    
    @staticmethod
    def to_model_dict(plan: PlanEntity) -> Dict[str, Any]:
        """转换领域实体为ORM模型字典"""
        return {
            "id": plan.id,
            "consultation_id": plan.consultationId,
            "customer_id": plan.customerId,
            "consultant_id": plan.consultantId,
            "status": plan.status.value,
            "title": plan.title,
            "content": plan.content,
            "version": plan.version,
            "created_at": plan.createdAt,
            "updated_at": plan.updatedAt,
            "metadata": dict(plan.metadata)
        }
