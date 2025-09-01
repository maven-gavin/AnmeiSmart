"""
顾问领域服务
处理顾问相关的业务逻辑
"""
from typing import Optional, Dict, Any
import logging

from .entities.consultant import Consultant

logger = logging.getLogger(__name__)


class ConsultantDomainService:
    """顾问领域服务 - 处理顾问相关的业务逻辑"""
    
    def __init__(self):
        pass
    
    def validate_consultant_creation(
        self,
        user_id: str,
        name: str,
        specialization: str,
        experience_years: int
    ) -> None:
        """验证顾问创建的有效性"""
        if not user_id or not user_id.strip():
            raise ValueError("用户ID不能为空")
        
        if not name or not name.strip():
            raise ValueError("顾问姓名不能为空")
        
        if len(name.strip()) > 100:
            raise ValueError("顾问姓名长度不能超过100个字符")
        
        if not specialization or not specialization.strip():
            raise ValueError("专业领域不能为空")
        
        if len(specialization.strip()) > 200:
            raise ValueError("专业领域长度不能超过200个字符")
        
        if experience_years < 0:
            raise ValueError("工作经验年数不能为负数")
        
        if experience_years > 50:
            raise ValueError("工作经验年数不能超过50年")
    
    def can_handle_consultation(
        self,
        consultant: Consultant,
        consultation_type: str
    ) -> bool:
        """检查顾问是否可以处理特定类型的咨询"""
        if not consultant.is_active:
            return False
        
        # 检查专业领域是否匹配
        supported_types = consultant.metadata.get("supported_consultation_types", [])
        return consultation_type in supported_types
    
    def get_consultant_workload(self, consultant: Consultant) -> Dict[str, Any]:
        """获取顾问工作负载信息"""
        # 这里可以添加获取顾问当前工作负载的逻辑
        # 例如：正在处理的咨询数量、方案数量等
        return {
            "consultant_id": consultant.id,
            "name": consultant.name,
            "specialization": consultant.specialization,
            "is_active": consultant.is_active,
            "workload": consultant.metadata.get("current_workload", 0)
        }
    
    def validate_consultant_profile_update(
        self,
        name: Optional[str] = None,
        specialization: Optional[str] = None,
        experience_years: Optional[int] = None
    ) -> None:
        """验证顾问资料更新的有效性"""
        if name is not None:
            if not name.strip():
                raise ValueError("顾问姓名不能为空")
            if len(name.strip()) > 100:
                raise ValueError("顾问姓名长度不能超过100个字符")
        
        if specialization is not None:
            if not specialization.strip():
                raise ValueError("专业领域不能为空")
            if len(specialization.strip()) > 200:
                raise ValueError("专业领域长度不能超过200个字符")
        
        if experience_years is not None:
            if experience_years < 0:
                raise ValueError("工作经验年数不能为负数")
            if experience_years > 50:
                raise ValueError("工作经验年数不能超过50年")
    
    def get_consultant_summary(self, consultant: Consultant) -> Dict[str, Any]:
        """获取顾问摘要信息"""
        return {
            "id": consultant.id,
            "user_id": consultant.user_id,
            "name": consultant.name,
            "specialization": consultant.specialization,
            "experience_years": consultant.experience_years,
            "is_active": consultant.is_active,
            "created_at": consultant.created_at,
            "updated_at": consultant.updated_at
        }
