"""
咨询相关依赖注入配置

使用清晰的业务术语，避免consultant和consultation的混淆。
从consultation_business.py导入所有依赖函数，避免重复定义。
"""

# 从consultation_business.py导入所有依赖函数，避免重复定义
from .consultation_business import (
    get_consultation_app_service,
    get_consultation_session_app_service,
    get_consultation_summary_app_service,
    get_plan_management_app_service,
    get_plan_generation_app_service
)

# 导出所有依赖函数
__all__ = [
    "get_consultation_app_service",
    "get_consultation_session_app_service", 
    "get_consultation_summary_app_service",
    "get_plan_management_app_service",
    "get_plan_generation_app_service"
]
