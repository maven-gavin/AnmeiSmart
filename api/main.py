# 先导入 bcrypt 补丁修复 passlib 问题
from app.core.bcrypt_patch import *

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
from datetime import datetime

from app.core.config import get_settings
from app.api.v1.api import api_router
from app.db.base import create_initial_roles, create_initial_system_settings

settings = get_settings()

# 定义应用生命周期管理器
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动时执行的初始化操作"""
    # 创建初始角色
    create_initial_roles()
    # 创建初始系统设置
    create_initial_system_settings()
    yield
    # 应用关闭时执行的清理操作

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