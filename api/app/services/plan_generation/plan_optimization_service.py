"""
方案优化服务 - 负责方案的优化和改进
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.db.models.plan_generation import PlanDraft
from app.schemas.plan_generation import (
    PlanDraftInfo,
    OptimizePlanRequest,
    PlanContent,
    PlanFeedback,
    PlanDraftStatus
)
from app.services.ai.ai_service import AIService

logger = logging.getLogger(__name__)


class PlanOptimizationService:
    """方案优化服务类 - 负责方案的优化和改进"""
    
    def __init__(self, db: Session):
        self.db = db
        self.ai_service = AIService()
    
    async def optimize_plan(
        self,
        request: OptimizePlanRequest,
        consultant_id: str
    ) -> PlanDraftInfo:
        """优化方案"""
        logger.info(f"开始优化方案: draft_id={request.draft_id}")
        
        # 获取原始草稿
        original_draft = self.db.query(PlanDraft).filter(
            PlanDraft.id == request.draft_id
        ).first()
        
        if not original_draft:
            raise ValueError(f"方案草稿不存在: {request.draft_id}")
        
        # 执行优化
        optimized_content = await self._optimize_plan_content(
            original_draft.content,
            request.optimization_type,
            request.requirements,
            request.feedback
        )
        
        # 创建新版本
        new_version = self._get_next_version(original_draft.session_id)
        
        optimized_draft = PlanDraft(
            session_id=original_draft.session_id,
            version=new_version,
            parent_version=original_draft.version,
            content=optimized_content,
            status=PlanDraftStatus.draft,
            generation_info={
                "generator": "ai",
                "optimization_type": request.optimization_type,
                "optimized_from": original_draft.id,
                "consultant_id": consultant_id,
                "optimization_time": datetime.now().isoformat()
            }
        )
        
        self.db.add(optimized_draft)
        self.db.commit()
        self.db.refresh(optimized_draft)
        
        logger.info(f"方案优化完成: new_draft_id={optimized_draft.id}")
        return PlanDraftInfo.from_model(optimized_draft)
    
    async def _optimize_plan_content(
        self,
        original_content: Dict[str, Any],
        optimization_type: str,
        requirements: Dict[str, Any],
        feedback: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """优化方案内容"""
        logger.info(f"优化方案内容: type={optimization_type}")
        
        try:
            # 构建优化请求
            optimization_request = {
                "original_content": original_content,
                "optimization_type": optimization_type,
                "requirements": requirements,
                "feedback": feedback or {}
            }
            
            # 调用AI服务进行优化
            optimized_content = await self.ai_service.optimize_plan(optimization_request)
            
            return optimized_content
            
        except Exception as e:
            logger.error(f"AI优化失败: {str(e)}")
            # 返回基于规则的优化结果
            return self._rule_based_optimization(
                original_content,
                optimization_type,
                requirements
            )
    
    def _rule_based_optimization(
        self,
        original_content: Dict[str, Any],
        optimization_type: str,
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """基于规则的优化"""
        logger.info("使用基于规则的优化")
        
        optimized_content = original_content.copy()
        
        if optimization_type == "cost":
            optimized_content = self._optimize_cost(optimized_content, requirements)
        elif optimization_type == "timeline":
            optimized_content = self._optimize_timeline(optimized_content, requirements)
        elif optimization_type == "content":
            optimized_content = self._optimize_content(optimized_content, requirements)
        
        return optimized_content
    
    def _optimize_cost(self, content: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """优化成本"""
        logger.info("优化成本")
        
        target_budget = requirements.get("target_budget")
        if not target_budget:
            return content
        
        # 简单的成本优化逻辑
        if "cost_breakdown" in content:
            cost_breakdown = content["cost_breakdown"]
            current_total = cost_breakdown.get("total_cost", 0)
            
            if current_total > target_budget:
                # 按比例调整费用
                reduction_ratio = target_budget / current_total
                
                cost_breakdown["treatment_costs"] = int(cost_breakdown.get("treatment_costs", 0) * reduction_ratio)
                cost_breakdown["product_costs"] = int(cost_breakdown.get("product_costs", 0) * reduction_ratio)
                cost_breakdown["maintenance_costs"] = int(cost_breakdown.get("maintenance_costs", 0) * reduction_ratio)
                cost_breakdown["total_cost"] = target_budget
                
                content["cost_breakdown"] = cost_breakdown
        
        return content
    
    def _optimize_timeline(self, content: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """优化时间线"""
        logger.info("优化时间线")
        
        # 简单的时间线优化逻辑
        if "timeline" in content and "preferred_duration" in requirements:
            timeline = content["timeline"]
            preferred_duration = requirements["preferred_duration"]
            
            # 调整完成日期
            if "completion_date" in timeline:
                timeline["completion_date"] = preferred_duration
            
            content["timeline"] = timeline
        
        return content
    
    def _optimize_content(self, content: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """优化内容"""
        logger.info("优化内容")
        
        # 根据要求调整内容
        if "focus_areas" in requirements:
            focus_areas = requirements["focus_areas"]
            
            # 更新目标关注点
            if "basic_info" in content:
                content["basic_info"]["target_concerns"] = focus_areas
        
        return content
    
    def _get_next_version(self, session_id: str) -> int:
        """获取下一个版本号"""
        max_version = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id
        ).order_by(PlanDraft.version.desc()).first()
        
        if max_version:
            return max_version.version + 1
        else:
            return 1
    
    def add_feedback(
        self,
        draft_id: str,
        feedback: PlanFeedback,
        feedback_type: str = "consultant"
    ) -> PlanDraftInfo:
        """添加反馈"""
        logger.info(f"添加反馈: draft_id={draft_id}, type={feedback_type}")
        
        draft = self.db.query(PlanDraft).filter(
            PlanDraft.id == draft_id
        ).first()
        
        if not draft:
            raise ValueError(f"方案草稿不存在: {draft_id}")
        
        # 更新反馈
        if not draft.feedback:
            draft.feedback = {}
        
        draft.feedback.update(feedback.dict())
        draft.updated_at = datetime.now()
        
        self.db.commit()
        self.db.refresh(draft)
        
        logger.info(f"反馈添加成功: {draft_id}")
        return PlanDraftInfo.from_model(draft)
    
    def get_optimization_history(
        self,
        session_id: str
    ) -> List[PlanDraftInfo]:
        """获取优化历史"""
        drafts = self.db.query(PlanDraft).filter(
            PlanDraft.session_id == session_id
        ).order_by(PlanDraft.version.asc()).all()
        
        return [PlanDraftInfo.from_model(draft) for draft in drafts]
    
    def compare_versions(
        self,
        draft_id1: str,
        draft_id2: str
    ) -> Dict[str, Any]:
        """比较版本差异"""
        logger.info(f"比较版本: {draft_id1} vs {draft_id2}")
        
        draft1 = self.db.query(PlanDraft).filter(PlanDraft.id == draft_id1).first()
        draft2 = self.db.query(PlanDraft).filter(PlanDraft.id == draft_id2).first()
        
        if not draft1 or not draft2:
            raise ValueError("方案草稿不存在")
        
        # 简单的差异比较
        differences = []
        
        # 比较基础信息
        if draft1.content.get("basic_info") != draft2.content.get("basic_info"):
            differences.append({
                "section": "basic_info",
                "type": "modified",
                "description": "基础信息已修改"
            })
        
        # 比较费用
        cost1 = draft1.content.get("cost_breakdown", {}).get("total_cost", 0)
        cost2 = draft2.content.get("cost_breakdown", {}).get("total_cost", 0)
        
        if cost1 != cost2:
            differences.append({
                "section": "cost_breakdown",
                "type": "modified",
                "description": f"总费用从 {cost1} 调整为 {cost2}"
            })
        
        return {
            "draft_id1": draft_id1,
            "draft_id2": draft_id2,
            "version1": draft1.version,
            "version2": draft2.version,
            "differences": differences
        } 