"""
客户模块依赖注入配置

遵循新架构标准：
- 使用FastAPI的依赖注入避免循环依赖
- 直接使用Service层，无需Repository抽象
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.customer.services.customer_service import CustomerService
from app.identity_access.deps.permission_deps import check_user_any_role


def get_customer_service(db: Session = Depends(get_db)) -> CustomerService:
    """获取客户服务实例"""
    return CustomerService(db)


async def check_customer_permission(user, required_roles: list[str]) -> bool:
    """检查客户权限"""
    return await check_user_any_role(user, required_roles)
