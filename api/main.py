# 先导入 bcrypt 补丁修复 passlib 问题
from app.core.bcrypt_patch import *

# 导入必要的库
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from datetime import datetime
import logging

from app.core.api import register_exception_handlers
from app.core.config import get_settings
from app.api import api_router
from app.common.infrastructure.db.base import create_initial_roles, create_initial_system_settings

# 导入新的WebSocket和Redis组件
from app.core.redis_client import redis_manager, get_redis_client
from app.websocket.broadcasting_factory import cleanup_broadcasting_services

# MessageBroadcaster会在需要时自动初始化

settings = get_settings()

# 配置日志级别为DEBUG，确保调试日志能够正确输出
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 定义应用生命周期管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时执行的初始化操作"""
    try:
        # 创建初始角色
        create_initial_roles()  # type: ignore
        # 创建初始系统设置
        create_initial_system_settings()  # type: ignore
        
        # 初始化Redis连接
        redis_client = await get_redis_client()
        logger.info("Redis连接已建立")
        
        # WebSocket连接管理器会在需要时自动初始化
        logger.info("WebSocket分布式连接管理器将在需要时初始化")
    
    except Exception as e:
        logger.error(f"应用启动初始化失败: {e}")
        raise
    
    yield
    
    # 应用关闭时执行的清理操作
    try:
        # 清理WebSocket连接管理器
        await cleanup_broadcasting_services()
        logger.info("WebSocket连接管理器已清理")
        
        # 关闭Redis连接
        await redis_manager.close()
        logger.info("Redis连接已关闭")
        
    except Exception as e:
        logger.error(f"应用关闭清理失败: {e}")

# 创建FastAPI应用并应用lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="安美智享客服系统后端API",
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册统一异常处理
register_exception_handlers(app)

# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

# OAuth发现端点需要在根路径可访问（MCP Inspector要求）
from app.mcp.endpoints.mcp_oauth import (
    oauth_metadata, oauth_metadata_options
)

# 添加根路径的OAuth授权服务器发现端点
app.add_api_route(
    "/.well-known/oauth-authorization-server",
    oauth_metadata,
    methods=["GET"],
    tags=["mcp-server"]
)

# 添加OPTIONS方法支持
app.add_api_route(
    "/.well-known/oauth-authorization-server",
    oauth_metadata_options,
    methods=["OPTIONS"],
    tags=["mcp-server"]
)

@app.get("/")
async def root() -> Dict[str, str]:
    """API根路径健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 