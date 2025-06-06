# 先导入 bcrypt 补丁修复 passlib 问题
from app.core.bcrypt_patch import *

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from datetime import datetime
import logging

from app.core.config import get_settings
from app.api.v1.api import api_router
from app.db.base import create_initial_roles, create_initial_system_settings

# 导入新的WebSocket和Redis组件
from app.core.redis_client import redis_manager, get_redis_client
from app.api.v1.endpoints.websocket import initialize_connection_manager, cleanup_connection_manager

settings = get_settings()
logger = logging.getLogger(__name__)

# 定义应用生命周期管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时执行的初始化操作"""
    try:
        # 创建初始角色
        create_initial_roles()
        # 创建初始系统设置
        create_initial_system_settings()
        
        # 初始化Redis连接
        redis_client = await get_redis_client()
        logger.info("Redis连接已建立")
        
        # 初始化WebSocket连接管理器
        await initialize_connection_manager(redis_client)
        logger.info("WebSocket分布式连接管理器已初始化")
        
    except Exception as e:
        logger.error(f"应用启动初始化失败: {e}")
        raise
    
    yield
    
    # 应用关闭时执行的清理操作
    try:
        # 清理WebSocket连接管理器
        await cleanup_connection_manager()
        logger.info("WebSocket连接管理器已清理")
        
        # 关闭Redis连接
        await redis_manager.close()
        logger.info("Redis连接已关闭")
        
    except Exception as e:
        logger.error(f"应用关闭清理失败: {e}")

# 创建FastAPI应用并应用lifespan
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="医美服务系统后端API",
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

# 包含API路由
app.include_router(api_router, prefix=settings.API_V1_STR)

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