import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from fastapi import status
from sqlalchemy.orm import Session
from typing import Dict, List

from app.core.config import get_settings
from main import app

settings = get_settings()

@pytest.mark.asyncio
async def test_login(async_client: AsyncClient, test_user: Dict[str, str]):
    """测试登录功能是否正常"""
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"],
    }
    response = await async_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data,
    )
    
    assert response.status_code == 200
    
    tokens = response.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient, test_user: dict) -> None:
    """测试密码错误"""
    login_data = {
        "username": test_user["email"],
        "password": "wrongpassword"
    }
    response = await async_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "邮箱或密码错误"

@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient) -> None:
    """测试不存在的用户"""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "testpassword123"
    }
    response = await async_client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "邮箱或密码错误"

@pytest.mark.asyncio
async def test_register_success(async_client: AsyncClient):
    """测试注册新用户"""
    user_data = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "12345678",
        "roles": ["customer"]
    }
    response = await async_client.post(f"{settings.API_V1_STR}/auth/register", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED

@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient, test_user: dict):
    """测试重复注册"""
    user_data = {
        "email": test_user["email"],
        "username": "newuser",
        "password": "12345678",
        "roles": ["customer"]
    }
    response = await async_client.post(f"{settings.API_V1_STR}/auth/register", json=user_data)
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_refresh_token(async_client: AsyncClient, test_user: dict):
    """测试刷新token"""
    # 登录获取token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    refresh_token = login_resp.json()["refresh_token"]
    # 刷新token
    resp = await async_client.post(f"{settings.API_V1_STR}/auth/refresh-token", json={"token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.json()["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_refresh_token_invalid(async_client: AsyncClient):
    """测试无效token刷新"""
    resp = await async_client.post(f"{settings.API_V1_STR}/auth/refresh-token", json={"token": "invalidtoken"})
    assert resp.status_code == 401

@pytest.mark.asyncio
async def test_get_me(async_client: AsyncClient, test_user: dict):
    """测试获取当前用户信息"""
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    resp = await async_client.get(f"{settings.API_V1_STR}/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_update_me(async_client: AsyncClient, test_user: dict):
    """测试更新当前用户信息"""
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    update_data = {"nickname": "新昵称"}
    resp = await async_client.put(f"{settings.API_V1_STR}/auth/me", json=update_data, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

@pytest.mark.asyncio
async def test_get_roles(async_client: AsyncClient, test_user: dict):
    """测试获取用户所有角色"""
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    resp = await async_client.get(f"{settings.API_V1_STR}/auth/roles", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

@pytest.mark.asyncio
async def test_switch_role(async_client: AsyncClient, test_user: dict):
    """测试切换角色"""
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = await async_client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    # 假设test_user有customer角色
    switch_data = {"role": "customer"}
    resp = await async_client.post(f"{settings.API_V1_STR}/auth/switch-role", json=switch_data, headers={"Authorization": f"Bearer {token}"})
    # 角色存在时应为200，否则403
    assert resp.status_code in (200, 403) 