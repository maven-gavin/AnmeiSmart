from fastapi import APIRouter

from app.api.v1.endpoints import chat, users, roles, auth, system, customer

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(roles.router, prefix="/roles", tags=["角色"])
api_router.include_router(chat.router, prefix="/chat", tags=["聊天"])
api_router.include_router(system.router, prefix="/system", tags=["系统"])
api_router.include_router(customer.router, prefix="/customers", tags=["客户"]) 