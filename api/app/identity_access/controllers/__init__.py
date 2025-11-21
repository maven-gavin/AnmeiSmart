from app.identity_access.controllers.users import router as users_router
from app.identity_access.controllers.roles import router as roles_router
from app.identity_access.controllers.auth import router as auth_router
from app.identity_access.controllers.tenants import router as tenants_router

# Re-export routers
__all__ = ["users_router", "roles_router", "auth_router", "tenants_router"]

