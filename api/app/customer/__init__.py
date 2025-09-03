"""
客户领域模块
"""

# 延迟导入避免循环依赖
__all__ = [
    "CustomerApplicationService",
    "CustomerDomainService", 
    "CustomerRepository",
    "CustomerProfileRepository",
    "CustomerConverter",
    "CustomerProfileConverter"
]

def __getattr__(name):
    """延迟导入避免循环依赖"""
    if name == "CustomerApplicationService":
        from .application.customer_application_service import CustomerApplicationService
        return CustomerApplicationService
    elif name == "CustomerDomainService":
        from .domain.customer_domain_service import CustomerDomainService
        return CustomerDomainService
    elif name == "CustomerRepository":
        from .infrastructure.repositories.customer_repository import CustomerRepository
        return CustomerRepository
    elif name == "CustomerProfileRepository":
        from .infrastructure.repositories.customer_profile_repository import CustomerProfileRepository
        return CustomerProfileRepository
    elif name == "CustomerConverter":
        from .converters.customer_converter import CustomerConverter
        return CustomerConverter
    elif name == "CustomerProfileConverter":
        from .converters.customer_profile_converter import CustomerProfileConverter
        return CustomerProfileConverter
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
