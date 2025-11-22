"""
数字人模块依赖注入配置

遵循新架构标准：
- 使用FastAPI的依赖注入避免循环依赖
- 直接使用Service层，无需Repository抽象
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.digital_humans.services.digital_human_service import DigitalHumanService


def get_digital_human_service(db: Session = Depends(get_db)) -> DigitalHumanService:
    """获取数字人服务实例"""
    return DigitalHumanService(db)

