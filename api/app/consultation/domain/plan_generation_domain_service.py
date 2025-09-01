"""
方案生成领域服务
处理方案生成相关的业务逻辑
"""
from typing import Optional, Dict, Any
import logging

from .entities.plan import Plan
from .value_objects.plan_status import PlanStatus

logger = logging.getLogger(__name__)


class PlanGenerationDomainService:
    """方案生成领域服务 - 处理方案生成相关的业务逻辑"""
    
    def __init__(self):
        pass
    
    def validate_plan_creation(
        self,
        consultation_id: str,
        customer_id: str,
        consultant_id: str,
        title: str,
        content: Dict[str, Any]
    ) -> None:
        """验证方案创建的有效性"""
        if not consultation_id or not consultation_id.strip():
            raise ValueError("咨询ID不能为空")
        
        if not customer_id or not customer_id.strip():
            raise ValueError("客户ID不能为空")
        
        if not consultant_id or not consultant_id.strip():
            raise ValueError("顾问ID不能为空")
        
        if not title or not title.strip():
            raise ValueError("方案标题不能为空")
        
        if len(title.strip()) > 200:
            raise ValueError("方案标题长度不能超过200个字符")
        
        if not content:
            raise ValueError("方案内容不能为空")
    
    def can_start_generation(self, plan: Plan) -> bool:
        """检查是否可以开始生成"""
        return plan.status == PlanStatus.DRAFT
    
    def can_complete_generation(self, plan: Plan) -> bool:
        """检查是否可以完成生成"""
        return plan.status == PlanStatus.GENERATING
    
    def can_approve_plan(self, plan: Plan) -> bool:
        """检查是否可以批准方案"""
        return plan.status == PlanStatus.REVIEWING
    
    def can_reject_plan(self, plan: Plan) -> bool:
        """检查是否可以拒绝方案"""
        return plan.status == PlanStatus.REVIEWING
    
    def validate_plan_content(self, content: Dict[str, Any]) -> None:
        """验证方案内容"""
        if not isinstance(content, dict):
            raise ValueError("方案内容必须是字典格式")
        
        required_fields = ["summary", "recommendations", "timeline"]
        for field in required_fields:
            if field not in content:
                raise ValueError(f"方案内容缺少必需字段: {field}")
        
        if not content.get("summary", "").strip():
            raise ValueError("方案摘要不能为空")
        
        if not content.get("recommendations"):
            raise ValueError("方案建议不能为空")
    
    def generate_plan_title(
        self,
        consultation_title: str,
        plan_type: Optional[str] = None
    ) -> str:
        """生成方案标题"""
        base_title = f"{consultation_title} - 方案"
        
        if plan_type:
            base_title += f" ({plan_type})"
        
        return base_title
    
    def get_plan_summary(self, plan: Plan) -> Dict[str, Any]:
        """获取方案摘要信息"""
        return {
            "id": plan.id,
            "title": plan.title,
            "status": plan.status.value,
            "consultation_id": plan.consultation_id,
            "customer_id": plan.customer_id,
            "consultant_id": plan.consultant_id,
            "version": plan.version,
            "created_at": plan.created_at,
            "updated_at": plan.updated_at
        }
