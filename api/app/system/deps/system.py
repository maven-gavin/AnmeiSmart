from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.system.services.system_service import SystemService


def get_system_service(db: Session = Depends(get_db)) -> SystemService:
    """获取系统服务实例"""
    return SystemService(db)
