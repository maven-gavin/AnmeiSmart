"""
任务类型值对象
"""
from enum import Enum
from typing import List, Dict, Any


class TaskType(str, Enum):
    """任务类型枚举"""
    # 用户相关任务
    NEW_USER_RECEPTION = "new_user_reception"
    CONSULTATION_UPGRADE = "consultation_upgrade"
    
    # 医疗相关任务
    PRESCRIPTION_REVIEW = "prescription_review"
    MEDICAL_CONSULTATION = "medical_consultation"
    
    # 运营相关任务
    SYSTEM_MAINTENANCE = "system_maintenance"
    USER_FEEDBACK = "user_feedback"
    
    # 通用任务
    GENERAL = "general"
    CUSTOM = "custom"
    
    @classmethod
    def get_medical_task_types(cls) -> List[str]:
        """获取医疗相关任务类型"""
        return [cls.PRESCRIPTION_REVIEW.value, cls.MEDICAL_CONSULTATION.value]
    
    @classmethod
    def get_consultant_task_types(cls) -> List[str]:
        """获取顾问相关任务类型"""
        return [cls.NEW_USER_RECEPTION.value, cls.CONSULTATION_UPGRADE.value]
    
    @classmethod
    def get_operator_task_types(cls) -> List[str]:
        """获取运营相关任务类型"""
        return [cls.SYSTEM_MAINTENANCE.value, cls.USER_FEEDBACK.value]
    
    @classmethod
    def get_task_type_metadata(cls, task_type: str) -> Dict[str, Any]:
        """获取任务类型元数据"""
        metadata = {
            cls.NEW_USER_RECEPTION.value: {
                "name": "新用户接待",
                "description": "新注册用户需要顾问主动联系提供咨询服务",
                "default_priority": "medium",
                "auto_assign": False
            },
            cls.CONSULTATION_UPGRADE.value: {
                "name": "咨询升级",
                "description": "用户咨询需要升级到更高级别服务",
                "default_priority": "high",
                "auto_assign": False
            },
            cls.PRESCRIPTION_REVIEW.value: {
                "name": "处方审核",
                "description": "医生处方需要审核确认",
                "default_priority": "high",
                "auto_assign": False
            },
            cls.MEDICAL_CONSULTATION.value: {
                "name": "医疗咨询",
                "description": "用户医疗相关问题咨询",
                "default_priority": "high",
                "auto_assign": False
            },
            cls.SYSTEM_MAINTENANCE.value: {
                "name": "系统维护",
                "description": "系统维护和优化任务",
                "default_priority": "medium",
                "auto_assign": False
            },
            cls.USER_FEEDBACK.value: {
                "name": "用户反馈",
                "description": "处理用户反馈和建议",
                "default_priority": "medium",
                "auto_assign": False
            }
        }
        
        return metadata.get(task_type, {
            "name": "通用任务",
            "description": "通用任务类型",
            "default_priority": "medium",
            "auto_assign": False
        })
    
    @classmethod
    def get_all_values(cls) -> List[str]:
        """获取所有任务类型值列表"""
        return [e.value for e in cls]