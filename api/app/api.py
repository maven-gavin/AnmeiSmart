from fastapi import APIRouter
from app.identity_access.endpoints import users,auth,roles,preferences
from app.chat.endpoints import  chat
from app.ai.endpoints import  ai, ai_gateway, agent_config
from app.system.endpoints import  system
from app.customer.endpoints import  customer
from app.websocket.endpoints import  websocket
from app.common.endpoints import  files
from app.consultation.endpoints import  consultation
from app.contacts.endpoints import  contacts
from app.mcp.endpoints import  mcp_config,mcp_server,mcp_oauth
from app.digital_humans.endpoints import  digital_humans,admin_digital_humans
from app.tasks.endpoints import  tasks

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

# 咨询业务路由（整合咨询会话、总结、方案管理、方案生成等所有咨询相关功能）
api_router.include_router(consultation.router, prefix="/consultation", tags=["consultation"])

# 文件上传路由
api_router.include_router(files.router, prefix="/files", tags=["files"])

# AI服务路由
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])

# 系统设置路由
api_router.include_router(system.router, prefix="/system", tags=["system"])

# 客户领域路由
api_router.include_router(customer.router, prefix="/customers", tags=["customers"])

# AI Gateway路由
api_router.include_router(ai_gateway.router, prefix="/ai-gateway", tags=["ai-gateway"])

# Agent配置管理路由
api_router.include_router(agent_config.router, prefix="/agent", tags=["agent-config"])

# MCP配置管理路由（管理员界面）
api_router.include_router(mcp_config.router, prefix="/mcp/admin", tags=["mcp-admin"])

# MCP服务器路由（对外提供MCP协议服务）
api_router.include_router(mcp_server.router, prefix="/mcp", tags=["mcp-server"])

# OAuth发现端点已在main.py中添加到根路径
api_router.include_router(mcp_oauth.router, prefix="/oauth", tags=["oauth-server"])

# 个人中心路由
api_router.include_router(preferences.router, prefix="/profile", tags=["profile"])

# 数字人管理路由
api_router.include_router(digital_humans.router, prefix="/digital-humans", tags=["digital-humans"])

# 管理员数字人管理路由
api_router.include_router(admin_digital_humans.router, prefix="/admin/digital-humans", tags=["admin-digital-humans"])

# 待办任务管理路由
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

# 通讯录管理路由
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])

# 后续可添加其他路由
# api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
# api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"])
# api_router.include_router(treatments.router, prefix="/treatments", tags=["treatments"])

# 在这里添加其他路由器
# api_router.include_router(services.router, prefix="/services", tags=["services"]) 