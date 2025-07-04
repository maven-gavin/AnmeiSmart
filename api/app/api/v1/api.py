from fastapi import APIRouter
from app.api.v1.endpoints import users, auth, roles, chat, ai, system, customer, websocket, files, consultation_summary, consultant

api_router = APIRouter()

# 认证相关路由
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# 用户管理路由
api_router.include_router(users.router, prefix="/users", tags=["users"])

# 角色管理路由
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])

# WebSocket连接路由 (注意：WebSocket端点不需要prefix)
api_router.include_router(websocket.router, tags=["websocket"])

# 聊天系统路由
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])

# 咨询总结路由
api_router.include_router(consultation_summary.router, prefix="/consultation", tags=["consultation-summary"])

# 文件上传路由
api_router.include_router(files.router, prefix="/files", tags=["files"])

# AI服务路由
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])

# 系统设置路由
api_router.include_router(system.router, prefix="/system", tags=["system"])

# 客户领域路由
api_router.include_router(customer.router, prefix="/customers", tags=["customers"])

# 顾问方案推荐路由
api_router.include_router(consultant.router, prefix="/consultant", tags=["consultant"])

# 后续可添加其他路由
# api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
# api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
# api_router.include_router(treatments.router, prefix="/treatments", tags=["treatments"])

# 在这里添加其他路由器
# api_router.include_router(services.router, prefix="/services", tags=["services"]) 