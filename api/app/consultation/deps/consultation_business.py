"""
咨询业务相关依赖注入配置
按照DDD分层架构，为不同的应用服务提供正确的依赖注入
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.infrastructure.db.base import get_db
from ..application import (
    ConsultationApplicationService,
    ConsultationSessionApplicationService,
    ConsultationSummaryApplicationService,
    PlanManagementApplicationService,
    PlanGenerationApplicationService
)
from ..infrastructure.repositories.consultation_repository import ConsultationRepository
from ..domain.consultation_domain_service import ConsultationDomainService
from app.chat.application.chat_application_service import ChatApplicationService
from app.chat.deps.chat import get_chat_application_service


def get_consultation_app_service(
    db: Session = Depends(get_db)
) -> ConsultationApplicationService:
    """获取咨询核心应用服务实例"""
    # 创建依赖
    consultation_repository = ConsultationRepository(db)
    consultation_domain_service = ConsultationDomainService()
    
    # 创建应用服务
    return ConsultationApplicationService(
        consultation_repository=consultation_repository,
        consultation_domain_service=consultation_domain_service
    )


def get_consultation_session_app_service(
    chat_app_service: ChatApplicationService = Depends(get_chat_application_service)
) -> ConsultationSessionApplicationService:
    """获取咨询会话应用服务实例"""
    return ConsultationSessionApplicationService(
        chat_application_service=chat_app_service
    )


def get_consultation_summary_app_service() -> ConsultationSummaryApplicationService:
    """获取咨询总结应用服务实例"""
    # TODO: 注入咨询总结相关的仓储和领域服务
    return ConsultationSummaryApplicationService()


def get_plan_management_app_service() -> PlanManagementApplicationService:
    """获取方案管理应用服务实例"""
    # TODO: 注入方案管理相关的仓储和领域服务
    return PlanManagementApplicationService()


def get_plan_generation_app_service() -> PlanGenerationApplicationService:
    """获取方案生成应用服务实例"""
    # TODO: 注入方案生成相关的仓储和领域服务
    return PlanGenerationApplicationService()
