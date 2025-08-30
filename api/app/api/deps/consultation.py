"""
咨询相关依赖注入配置
使用清晰的业务术语，避免consultant和consultation的混淆
"""
from typing import Optional
from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.consultation.application import ConsultationApplicationService
from app.services.consultation.infrastructure.repositories.consultation_repository import ConsultationRepository
from app.services.consultation.domain.consultation_domain_service import ConsultationDomainService


def get_consultation_app_service(
    db: Session = Depends(get_db)
) -> ConsultationApplicationService:
    """获取咨询业务应用服务实例"""
    # 创建依赖
    consultation_repository = ConsultationRepository(db)
    consultation_domain_service = ConsultationDomainService()
    
    # 创建应用服务
    return ConsultationApplicationService(
        consultation_repository=consultation_repository,
        consultation_domain_service=consultation_domain_service
    )
