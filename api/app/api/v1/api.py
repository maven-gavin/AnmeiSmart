from fastapi import APIRouter
from app.api.v1.endpoints import users, auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])

# 在这里添加其他路由器
# api_router.include_router(services.router, prefix="/services", tags=["services"]) 