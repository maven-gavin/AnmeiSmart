from fastapi import Depends
from sqlalchemy.orm import Session

from app.common.infrastructure.db.base import get_db
from app.identity_access.services.user_service import UserService
from app.identity_access.services.auth_service import AuthService
from app.identity_access.services.role_service import RoleService

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)

def get_role_service(db: Session = Depends(get_db)) -> RoleService:
    return RoleService(db)
