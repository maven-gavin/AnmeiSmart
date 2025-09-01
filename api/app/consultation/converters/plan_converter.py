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
from ..domain.entities.plan import Plan
from ..domain.value_objects.plan_status import PlanStatus


class PlanConverter:
    """方案数据转换器"""
    
    @staticmethod
    def to_response(plan: Plan) -> PlanResponse:
        """转换方案实体为响应格式"""
        return PlanResponse(
            id=plan.id,
            consultation_id=plan.consultation_id,
            customer_id=plan.customer_id,
            consultant_id=plan.consultant_id,
            status=plan.status.value,
            title=plan.title,
            content=plan.content,
            version=plan.version,
            created_at=plan.created_at,
            updated_at=plan.updated_at,
            metadata=plan.metadata
        )
    
    @staticmethod
    def to_list_response(plans: List[Plan]) -> PlanListResponse:
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
            "consultation_id": request.consultation_id,
            "customer_id": request.customer_id,
            "consultant_id": request.consultant_id,
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
    def from_model(model) -> Plan:
        """从ORM模型转换为领域实体"""
        return Plan(
            id=model.id,
            consultation_id=model.consultation_id,
            customer_id=model.customer_id,
            consultant_id=model.consultant_id,
            status=PlanStatus.from_string(model.status),
            title=model.title,
            content=model.content,
            version=model.version,
            created_at=model.created_at,
            updated_at=model.updated_at,
            metadata=model.metadata or {}
        )
    
    @staticmethod
    def to_model_dict(plan: Plan) -> Dict[str, Any]:
        """转换领域实体为ORM模型字典"""
        return {
            "id": plan.id,
            "consultation_id": plan.consultation_id,
            "customer_id": plan.customer_id,
            "consultant_id": plan.consultant_id,
            "status": plan.status.value,
            "title": plan.title,
            "content": plan.content,
            "version": plan.version,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at,
            "metadata": plan.metadata
        }
