from fastapi import APIRouter
from app.api.v1.endpoints import users, auth, roles, chat, ai, system

api_router = APIRouter()

# 认证相关路由
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# 用户管理路由
api_router.include_router(users.router, prefix="/users", tags=["users"])

# 角色管理路由
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])

# 聊天系统路由
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])

# AI服务路由
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])

# 系统设置路由
api_router.include_router(system.router, prefix="/system", tags=["system"])

# 后续可添加其他路由
# api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
# api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
# api_router.include_router(treatments.router, prefix="/treatments", tags=["treatments"])

# 在这里添加其他路由器
# api_router.include_router(services.router, prefix="/services", tags=["services"]) 