"""
咨询领域服务
处理跨聚合的咨询业务逻辑
"""
from typing import Optional, Dict, Any
import logging

from .entities.consultation import ConsultationEntity
from .value_objects.consultation_status import ConsultationStatus

logger = logging.getLogger(__name__)


class ConsultationDomainService:
    """咨询领域服务 - 处理跨聚合的业务逻辑"""
    
    def __init__(self):
        pass
    
    def validate_consultation_creation(
        self,
        customer_id: str,
        title: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """验证咨询创建的有效性"""
        if not customer_id or not customer_id.strip():
            raise ValueError("客户ID不能为空")
        
        if not title or not title.strip():
            raise ValueError("咨询标题不能为空")
        
        if len(title.strip()) > 200:
            raise ValueError("咨询标题长度不能超过200个字符")
        
        # 可以添加更多业务规则验证
        # 例如：检查客户是否有未完成的咨询
        # 例如：检查客户权限等
    
    def can_assign_consultant(
        self,
        consultation: ConsultationEntity,
        consultant_id: str
    ) -> bool:
        """检查是否可以分配顾问"""
        # 检查咨询状态
        if not consultation.status.is_active():
            return False
        
        # 检查是否已经分配了顾问
        if consultation.consultantId:
            return False
        
        # 可以添加更多业务规则
        # 例如：检查顾问是否可用
        # 例如：检查顾问专业领域是否匹配
        
        return True
    
    def can_complete_consultation(self, consultation: ConsultationEntity) -> bool:
        """检查是否可以完成咨询"""
        # 检查咨询状态
        if not consultation.status.can_transition_to(ConsultationStatus.COMPLETED):
            return False
        
        # 检查是否已分配顾问
        if not consultation.consultantId:
            return False
        
        # 可以添加更多业务规则
        # 例如：检查是否有未完成的方案
        # 例如：检查客户满意度等
        
        return True
    
    def can_cancel_consultation(self, consultation: ConsultationEntity) -> bool:
        """检查是否可以取消咨询"""
        # 检查咨询状态
        if not consultation.status.can_transition_to(ConsultationStatus.CANCELLED):
            return False
        
        # 可以添加更多业务规则
        # 例如：检查是否有已批准的方案
        # 例如：检查取消时间限制等
        
        return True
    
    def generate_consultation_title(
        self,
        customer_name: str,
        consultation_type: Optional[str] = None
    ) -> str:
        """生成咨询标题"""
        base_title = f"{customer_name} 的咨询"
        
        if consultation_type:
            base_title += f" - {consultation_type}"
        
        return base_title
    
    def calculate_consultation_duration(
        self,
        consultation: ConsultationEntity
    ) -> Optional[int]:
        """计算咨询持续时间（分钟）"""
        if consultation.status == ConsultationStatus.PENDING:
            return None
        
        # 计算从创建到完成的时间
        if consultation.status == ConsultationStatus.COMPLETED:
            duration = consultation.updatedAt - consultation.createdAt
            return int(duration.total_seconds() / 60)
        
        # 计算从创建到当前的时间
        from datetime import datetime
        duration = datetime.utcnow() - consultation.createdAt
        return int(duration.total_seconds() / 60)
    
    def validate_consultation_metadata(
        self,
        metadata: Dict[str, Any]
    ) -> None:
        """验证咨询元数据"""
        # 检查元数据大小
        import json
        metadata_size = len(json.dumps(metadata))
        if metadata_size > 10000:  # 10KB限制
            raise ValueError("咨询元数据过大")
        
        # 检查敏感字段
        sensitive_fields = ["password", "token", "secret"]
        for field in sensitive_fields:
            if field in metadata:
                raise ValueError(f"元数据中不能包含敏感字段: {field}")
    
    def get_consultation_summary(self, consultation: ConsultationEntity) -> Dict[str, Any]:
        """获取咨询摘要信息"""
        return {
            "id": consultation.id,
            "title": consultation.title,
            "status": consultation.status.value,
            "customer_id": consultation.customerId,
            "consultant_id": consultation.consultantId,
            "created_at": consultation.createdAt,
            "updated_at": consultation.updatedAt,
            "duration_minutes": self.calculate_consultation_duration(consultation)
        }
