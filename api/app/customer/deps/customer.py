"""
客户模块依赖注入配置

遵循 @ddd_service_schema.mdc 第3章依赖注入配置规范：
- 使用FastAPI的依赖注入避免循环依赖
- 接口抽象：使用抽象接口而不是具体实现
- 依赖方向：确保依赖方向指向领域层
- 生命周期管理：合理管理依赖的作用域
"""

from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.customer.infrastructure.repositories.customer_repository import CustomerRepository
from app.customer.application.customer_application_service import CustomerApplicationService


def get_customer_repository(db: Session = Depends(get_db)) -> CustomerRepository:
    """获取客户仓储实例
    
    遵循DDD规范：
    - 使用FastAPI的依赖注入避免循环依赖
    - 依赖方向：确保依赖方向指向领域层
    """
    return CustomerRepository(db)


def get_customer_application_service(
    customer_repository: CustomerRepository = Depends(get_customer_repository)
) -> CustomerApplicationService:
    """获取客户应用服务实例
    
    遵循DDD规范：
    - 编排领域服务，实现用例，事务管理
    - 无状态，协调领域对象完成业务用例
    """
    return CustomerApplicationService(
        customer_repository=customer_repository
    )