from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from fastapi import HTTPException, status

from app.db.models.consultant import (
    PersonalizedPlan, ProjectType, SimulationImage, 
    ProjectTemplate, CustomerPreference, PlanVersion
)
from app.schemas.consultant import (
    PersonalizedPlanResponse, PersonalizedPlanCreate, PersonalizedPlanUpdate,
    ProjectTypeResponse, SimulationImageResponse,
    ProjectTemplateResponse, CustomerPreferenceResponse,
    RecommendationRequest, RecommendationResponse
)


class ConsultantService:
    """顾问服务类 - 处理顾问相关业务逻辑"""
    
    def __init__(self, db: Session):
        self.db = db

    # 个性化方案管理
    def get_all_plans(self, consultant_id: Optional[str] = None) -> List[PersonalizedPlanResponse]:
        """获取所有个性化方案"""
        query = self.db.query(PersonalizedPlan)
        if consultant_id:
            query = query.filter(PersonalizedPlan.consultant_id == consultant_id)
        
        plans = query.order_by(desc(PersonalizedPlan.created_at)).all()
        return [PersonalizedPlanResponse.from_model(plan) for plan in plans]

    def get_plan_by_id(self, plan_id: str) -> PersonalizedPlanResponse:
        """根据ID获取个性化方案"""
        plan = self.db.query(PersonalizedPlan).filter(PersonalizedPlan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"方案 {plan_id} 不存在")
        
        return PersonalizedPlanResponse.from_model(plan)

    def get_customer_plans(self, customer_id: str) -> List[PersonalizedPlanResponse]:
        """获取客户的所有方案"""
        plans = self.db.query(PersonalizedPlan).filter(
            PersonalizedPlan.customer_id == customer_id
        ).order_by(desc(PersonalizedPlan.created_at)).all()
        
        return [PersonalizedPlanResponse.from_model(plan) for plan in plans]

    def create_plan(self, plan_data: PersonalizedPlanCreate, consultant_id: str, consultant_name: str) -> PersonalizedPlanResponse:
        """创建个性化方案"""
        # 计算总费用
        total_cost = sum(project.cost for project in plan_data.projects)
        
        # 创建方案
        plan = PersonalizedPlan(
            customer_id=plan_data.customer_id,
            customer_name=plan_data.customer_name,
            consultant_id=consultant_id,
            consultant_name=consultant_name,
            customer_profile=plan_data.customer_profile.model_dump() if plan_data.customer_profile else None,
            projects=[project.model_dump() for project in plan_data.projects],
            total_cost=total_cost,
            estimated_timeframe=plan_data.estimated_timeframe,
            notes=plan_data.notes
        )
        
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        
        # 创建初始版本 - 暂时注释掉，避免版本表问题
        # self._create_plan_version(plan.id, 1, plan.projects, plan.total_cost, "初始版本")
        
        return PersonalizedPlanResponse.from_model(plan)

    def update_plan(self, plan_id: str, plan_data: PersonalizedPlanUpdate) -> PersonalizedPlanResponse:
        """更新个性化方案"""
        plan = self.db.query(PersonalizedPlan).filter(PersonalizedPlan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"方案 {plan_id} 不存在")
        
        # 记录更新前的状态用于版本控制
        old_projects = plan.projects
        old_total_cost = plan.total_cost
        
        # 更新字段
        if plan_data.customer_profile is not None:
            plan.customer_profile = plan_data.customer_profile.model_dump()
        
        if plan_data.projects is not None:
            plan.projects = [project.model_dump() for project in plan_data.projects]
            plan.total_cost = sum(project.cost for project in plan_data.projects)
        
        if plan_data.estimated_timeframe is not None:
            plan.estimated_timeframe = plan_data.estimated_timeframe
        
        if plan_data.status is not None:
            plan.status = plan_data.status
        
        if plan_data.notes is not None:
            plan.notes = plan_data.notes
        
        self.db.commit()
        self.db.refresh(plan)
        
        # 如果项目或费用发生变化，创建新版本 - 暂时注释掉
        # if plan_data.projects and (old_projects != plan.projects or old_total_cost != plan.total_cost):
        #     latest_version = self._get_latest_version_number(plan_id)
        #     self._create_plan_version(
        #         plan_id, 
        #         latest_version + 1, 
        #         plan.projects, 
        #         plan.total_cost, 
        #         "方案更新"
        #     )
        
        return PersonalizedPlanResponse.from_model(plan)

    def delete_plan(self, plan_id: str) -> bool:
        """删除个性化方案"""
        plan = self.db.query(PersonalizedPlan).filter(PersonalizedPlan.id == plan_id).first()
        if not plan:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"方案 {plan_id} 不存在")
        
        self.db.delete(plan)
        self.db.commit()
        return True

    # 项目类型管理
    def get_all_project_types(self, active_only: bool = True) -> List[ProjectTypeResponse]:
        """获取所有项目类型"""
        query = self.db.query(ProjectType)
        if active_only:
            query = query.filter(ProjectType.is_active == True)
        
        project_types = query.order_by(ProjectType.category, ProjectType.name).all()
        return [ProjectTypeResponse.from_model(pt) for pt in project_types]

    def get_project_type_by_id(self, project_type_id: str) -> ProjectTypeResponse:
        """根据ID获取项目类型"""
        project_type = self.db.query(ProjectType).filter(ProjectType.id == project_type_id).first()
        if not project_type:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"项目类型 {project_type_id} 不存在")
        
        return ProjectTypeResponse.from_model(project_type)

    # 项目模板管理
    def get_all_project_templates(self, category: Optional[str] = None, active_only: bool = True) -> List[ProjectTemplateResponse]:
        """获取所有项目模板"""
        query = self.db.query(ProjectTemplate)
        if active_only:
            query = query.filter(ProjectTemplate.is_active == True)
        if category:
            query = query.filter(ProjectTemplate.category == category)
        
        templates = query.order_by(ProjectTemplate.category, ProjectTemplate.name).all()
        return [ProjectTemplateResponse.from_model(template) for template in templates]

    def get_suitable_templates(self, customer_profile: Dict[str, Any]) -> List[ProjectTemplateResponse]:
        """根据客户画像获取合适的项目模板"""
        query = self.db.query(ProjectTemplate).filter(ProjectTemplate.is_active == True)
        
        # 根据年龄筛选
        age = customer_profile.get('age')
        if age:
            query = query.filter(
                and_(
                    or_(ProjectTemplate.suitable_age_min.is_(None), ProjectTemplate.suitable_age_min <= age),
                    or_(ProjectTemplate.suitable_age_max.is_(None), ProjectTemplate.suitable_age_max >= age)
                )
            )
        
        # 根据预算筛选（基础筛选）
        budget = customer_profile.get('budget')
        if budget:
            query = query.filter(ProjectTemplate.base_cost <= budget * 1.2)  # 允许20%的预算弹性
        
        templates = query.order_by(ProjectTemplate.base_cost).all()
        
        # 进一步根据关注问题筛选
        concerns = customer_profile.get('concerns', [])
        if concerns:
            filtered_templates = []
            for template in templates:
                if template.suitable_concerns:
                    # 检查是否有匹配的关注问题
                    if any(concern in template.suitable_concerns for concern in concerns):
                        filtered_templates.append(template)
                else:
                    # 如果模板没有限制，也包含在内
                    filtered_templates.append(template)
            templates = filtered_templates
        
        return [ProjectTemplateResponse.from_model(template) for template in templates]

    # 智能推荐
    def generate_recommendations(self, request: RecommendationRequest) -> RecommendationResponse:
        """生成个性化方案推荐"""
        # 获取合适的项目模板
        suitable_templates = self.get_suitable_templates(request.customer_profile.model_dump())
        
        # 计算推荐分数和总费用
        total_cost = 0
        recommended_projects = []
        confidence_scores = []
        
        for template in suitable_templates[:5]:  # 限制推荐数量
            # 简单的推荐算法（后续可以用AI增强）
            score = self._calculate_recommendation_score(template, request.customer_profile)
            if score > 0.3:  # 阈值过滤
                recommended_projects.append(template)
                total_cost += template.base_cost
                confidence_scores.append(score)
        
        # 计算整体置信度
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        # 生成推荐理由
        reasoning = self._generate_reasoning(recommended_projects, request.customer_profile)
        
        return RecommendationResponse(
            recommended_projects=recommended_projects,
            total_estimated_cost=total_cost,
            confidence_score=overall_confidence,
            reasoning=reasoning
        )

    # 私有辅助方法
    def _create_plan_version(self, plan_id: str, version_number: int, projects: List[Dict], total_cost: float, notes: str):
        """创建方案版本记录"""
        version = PlanVersion(
            plan_id=plan_id,
            version_number=version_number,
            projects=projects,
            total_cost=total_cost,
            notes=notes
        )
        self.db.add(version)
        self.db.commit()

    def _get_latest_version_number(self, plan_id: str) -> int:
        """获取最新版本号"""
        latest_version = self.db.query(PlanVersion).filter(
            PlanVersion.plan_id == plan_id
        ).order_by(desc(PlanVersion.version_number)).first()
        
        return latest_version.version_number if latest_version else 0

    def _calculate_recommendation_score(self, template: ProjectTemplate, customer_profile) -> float:
        """计算推荐分数"""
        score = 0.5  # 基础分数
        
        # 根据预算匹配度计分
        if customer_profile.budget and template.base_cost <= customer_profile.budget:
            budget_ratio = template.base_cost / customer_profile.budget
            if budget_ratio <= 0.7:
                score += 0.3
            elif budget_ratio <= 0.9:
                score += 0.2
            else:
                score += 0.1
        
        # 根据关注问题匹配度计分
        if customer_profile.concerns and template.suitable_concerns:
            matches = len(set(customer_profile.concerns) & set(template.suitable_concerns))
            if matches > 0:
                score += 0.2 * matches / len(customer_profile.concerns)
        
        return min(score, 1.0)  # 确保分数不超过1

    def _generate_reasoning(self, recommended_projects: List[ProjectTemplateResponse], customer_profile) -> str:
        """生成推荐理由"""
        if not recommended_projects:
            return "根据您的需求，暂时没有找到完全匹配的项目。建议调整预算或需求后重新咨询。"
        
        reasons = []
        reasons.append(f"根据您{customer_profile.age}岁的年龄特点")
        
        if customer_profile.concerns:
            concerns_str = "、".join(customer_profile.concerns)
            reasons.append(f"针对您关心的{concerns_str}问题")
        
        if customer_profile.budget:
            reasons.append(f"结合您¥{customer_profile.budget:,.0f}的预算范围")
        
        project_names = "、".join([p.name for p in recommended_projects])
        
        return f"{'，'.join(reasons)}，为您推荐了{project_names}等项目。这些项目具有良好的安全性和效果保障，符合您的个人需求和期望。" 