from fastapi import APIRouter
from app.identity_access.controllers import users, auth, roles, tenants, resources, permissions
from app.chat.controllers import chat
from app.ai.controllers import ai_gateway, agent_config, agent_chat
from app.system.controllers import system
from app.customer.controllers import customer
from app.websocket.controllers import websocket
from app.common.controllers import files
from app.contacts.controllers import contacts
from app.mcp.controllers import mcp_config, mcp_server, mcp_oauth
from app.digital_humans.controllers import digital_humans, admin_digital_humans
from app.tasks.controllers import tasks
from app.channels.controllers import webhook as channel_webhook

api_router = APIRouter()

# 认证相关路由
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# 用户管理路由
api_router.include_router(users.router, prefix="/users", tags=["users"])

# 角色管理路由
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])

# 租户管理路由
api_router.include_router(tenants.router, tags=["tenants"])

# 资源管理路由
api_router.include_router(resources.router, prefix="/resources", tags=["resources"])

# 权限管理路由
api_router.include_router(permissions.router, prefix="/permissions", tags=["permissions"])

# WebSocket连接路由 (注意：WebSocket端点不需要prefix)
api_router.include_router(websocket.router, tags=["websocket"])

# 聊天系统路由
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])


# 文件上传路由
api_router.include_router(files.router, prefix="/files", tags=["files"])

# 系统设置路由
api_router.include_router(system.router, prefix="/system", tags=["system"])

# 客户领域路由
api_router.include_router(customer.router, prefix="/customers", tags=["customers"])

# AI Gateway路由
api_router.include_router(ai_gateway.router, prefix="/ai-gateway", tags=["ai-gateway"])

# Agent配置管理路由
api_router.include_router(agent_config.router, prefix="/agent", tags=["agent-config"])

# Agent对话路由
api_router.include_router(agent_chat.router, prefix="/agent", tags=["agent-chat"])

# MCP配置管理路由（管理员界面）
api_router.include_router(mcp_config.router, prefix="/mcp/admin", tags=["mcp-admin"])

# MCP服务器路由（对外提供MCP协议服务）
api_router.include_router(mcp_server.router, prefix="/mcp", tags=["mcp-server"])

# OAuth发现端点已在main.py中添加到根路径
api_router.include_router(mcp_oauth.router, prefix="/oauth", tags=["oauth-server"])

# 个人中心路由 (已合并到 users /me)
# api_router.include_router(preferences.router, prefix="/profile", tags=["profile"])

# 数字人管理路由
api_router.include_router(digital_humans.router, prefix="/digital-humans", tags=["digital-humans"])

# 管理员数字人管理路由
api_router.include_router(admin_digital_humans.router, prefix="/admin/digital-humans", tags=["admin-digital-humans"])

# 待办任务管理路由
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])

# 通讯录管理路由
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])

# 渠道Webhook路由
api_router.include_router(channel_webhook.router, tags=["channels"])

# 后续可添加其他路由

# 在这里添加其他路由器
# api_router.include_router(services.router, prefix="/services", tags=["services"])
