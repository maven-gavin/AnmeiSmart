"""
客户服务模块 - 新架构
"""

# 导出控制器
from .controllers import customer_router

# 导出模型
from .models import Customer, CustomerProfile

# 导出服务
from .services import CustomerService

__all__ = [
    "customer_router",
    "Customer",
    "CustomerProfile",
    "CustomerService",
]
