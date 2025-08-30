"""
个性化方案数据转换器
"""
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.schemas.consultation import (
    PersonalizedPlanResponse, PersonalizedPlanCreate, PersonalizedPlanUpdate,
    ProjectTypeResponse, ProjectTemplateResponse, SimulationImageResponse,
    CustomerProfile, ProjectDetail, SimulationParameter
)
from app.db.models.consultant import (
    PersonalizedPlan, ProjectType, ProjectTemplate, SimulationImage
)


class PersonalizedPlanConverter:
    """个性化方案数据转换器"""
    
    @staticmethod
    def to_response(plan: PersonalizedPlan) -> PersonalizedPlanResponse:
        """转换个性化方案ORM模型为响应格式"""
        # 转换customer_profile JSON
        customer_profile = None
        if plan.customer_profile:
            customer_profile = CustomerProfile(**plan.customer_profile)
        
        # 转换projects JSON为ProjectDetail列表
        projects = []
        if plan.projects:
            for project_data in plan.projects:
                projects.append(ProjectDetail(**project_data))
        
        return PersonalizedPlanResponse(
            id=plan.id,
            customer_id=plan.customer_id,
            customer_name=plan.customer_name,
            consultant_id=plan.consultant_id,
            consultant_name=plan.consultant_name,
            customer_profile=customer_profile,
            projects=projects,
            total_cost=plan.total_cost,
            estimated_timeframe=plan.estimated_timeframe,
            status=plan.status,
            notes=plan.notes,
            created_at=plan.created_at,
            updated_at=plan.updated_at
        )
    
    @staticmethod
    def from_create_request(request: PersonalizedPlanCreate) -> Dict[str, Any]:
        """从创建请求转换为ORM模型参数"""
        return {
            "customer_id": request.customer_id,
            "customer_name": request.customer_name,
            "customer_profile": request.customer_profile.model_dump() if request.customer_profile else None,
            "projects": [project.model_dump() for project in request.projects],
            "estimated_timeframe": request.estimated_timeframe,
            "notes": request.notes
        }
    
    @staticmethod
    def from_update_request(request: PersonalizedPlanUpdate) -> Dict[str, Any]:
        """从更新请求转换为ORM模型参数"""
        update_data = {}
        
        if request.customer_profile is not None:
            update_data["customer_profile"] = request.customer_profile.model_dump()
        
        if request.projects is not None:
            update_data["projects"] = [project.model_dump() for project in request.projects]
        
        if request.estimated_timeframe is not None:
            update_data["estimated_timeframe"] = request.estimated_timeframe
        
        if request.status is not None:
            update_data["status"] = request.status
        
        if request.notes is not None:
            update_data["notes"] = request.notes
        
        return update_data


class ProjectTypeConverter:
    """项目类型数据转换器"""
    
    @staticmethod
    def to_response(project_type: ProjectType) -> ProjectTypeResponse:
        """转换项目类型ORM模型为响应格式"""
        # 转换parameters JSON为SimulationParameter列表
        parameters = []
        if project_type.parameters:
            for param_data in project_type.parameters:
                parameters.append(SimulationParameter(**param_data))
        
        return ProjectTypeResponse(
            id=project_type.id,
            name=project_type.name,
            label=project_type.label,
            description=project_type.description,
            parameters=parameters,
            is_active=project_type.is_active,
            category=project_type.category,
            created_at=project_type.created_at,
            updated_at=project_type.updated_at
        )


class ProjectTemplateConverter:
    """项目模板数据转换器"""
    
    @staticmethod
    def to_response(template: ProjectTemplate) -> ProjectTemplateResponse:
        """转换项目模板ORM模型为响应格式"""
        return ProjectTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            category=template.category,
            base_cost=template.base_cost,
            duration=template.duration,
            recovery_time=template.recovery_time,
            expected_results=template.expected_results,
            risks=template.risks or [],
            is_active=template.is_active,
            suitable_age_min=template.suitable_age_min,
            suitable_age_max=template.suitable_age_max,
            suitable_concerns=template.suitable_concerns or [],
            created_at=template.created_at,
            updated_at=template.updated_at
        )


class SimulationImageConverter:
    """术前模拟图像数据转换器"""
    
    @staticmethod
    def to_response(simulation_image: SimulationImage) -> SimulationImageResponse:
        """转换术前模拟图像ORM模型为响应格式"""
        return SimulationImageResponse(
            id=simulation_image.id,
            customer_id=simulation_image.customer_id,
            customer_name=simulation_image.customer_name,
            original_image_path=simulation_image.original_image_path,
            simulated_image_path=simulation_image.simulated_image_path,
            project_type_id=simulation_image.project_type_id,
            parameters=simulation_image.parameters,
            notes=simulation_image.notes,
            consultant_id=simulation_image.consultant_id,
            created_at=simulation_image.created_at,
            updated_at=simulation_image.updated_at
        )
