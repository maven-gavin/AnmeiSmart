"""
接口定义层 - 用户身份与权限上下文

定义所有服务接口，包括仓储接口、领域服务接口、应用服务接口。
遵循依赖倒置原则，上层通过接口依赖下层。
"""

from .repository_interfaces import (
    IUserRepository,
    IRoleRepository,
    ILoginHistoryRepository
)
from .domain_service_interfaces import (
    IUserDomainService,
    IAuthenticationDomainService,
    IPermissionDomainService
)
from .application_service_interfaces import (
    IIdentityAccessApplicationService
)

__all__ = [
    # 仓储接口
    "IUserRepository",
    "IRoleRepository", 
    "ILoginHistoryRepository",
    
    # 领域服务接口
    "IUserDomainService",
    "IAuthenticationDomainService",
    "IPermissionDomainService",
    
    # 应用服务接口
    "IIdentityAccessApplicationService"
]
