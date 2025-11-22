"""
联系人模块依赖注入配置

遵循新架构标准：
- 使用FastAPI的依赖注入避免循环依赖
- 直接使用Service层，无需Repository抽象
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.contacts.services.contact_service import ContactService


def get_contact_service(db: Session = Depends(get_db)) -> ContactService:
    """获取联系人服务实例"""
    return ContactService(db)
