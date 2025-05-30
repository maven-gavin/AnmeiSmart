import pytest
from fastapi import status
from sqlalchemy.orm import Session
from typing import Dict, Generator
from httpx import AsyncClient

from app.db.models.user import User, Role
from app.services import user_service
from app.core.security import create_access_token
from app.schemas.user import UserCreate, UserUpdate
from app.main import app

# 测试数据
test_admin = {
    "email": "admin@test.com",
    "username": "admin",
    "password": "admin123456",
    "roles": ["admin"]
}

test_user = {
    "email": "user@test.com", 
    "username": "testuser",
    "password": "test123456",
    "roles": ["customer"]
}

test_user_update = {
    "username": "updated_user",
    "phone": "1234567890"
}

@pytest.fixture
async def admin_token(db: Session) -> str:
    """创建管理员用户并返回token"""
    # 创建管理员用户
    admin_in = UserCreate(**test_admin)
    admin = await user_service.create(db, obj_in=admin_in)
    return create_access_token(admin.id)

@pytest.fixture
async def user_token(db: Session) -> str:
    """创建普通用户并返回token"""
    user_in = UserCreate(**test_user)
    user = await user_service.create(db, obj_in=user_in)
    return create_access_token(user.id)

@pytest.fixture
async def async_client():
    """创建异步HTTP客户端"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_create_user(async_client, admin_token):
    """测试创建用户接口"""
    token = await admin_token
    headers = {"Authorization": f"Bearer {token}"}
    new_user = {
        "email": "newuser@test.com",
        "username": "newuser",
        "password": "newuser123",
        "roles": ["customer"]
    }
    
    response = await async_client.post(
        "/api/v1/users/",
        headers=headers,
        json=new_user
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == new_user["email"]
    assert data["username"] == new_user["username"]
    assert "password" not in data
    assert "customer" in data["roles"]

@pytest.mark.asyncio
async def test_create_user_existing_email(async_client, admin_token):
    """测试创建已存在邮箱的用户"""
    token = await admin_token
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await async_client.post(
        "/api/v1/users/",
        headers=headers,
        json=test_user
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "该邮箱已被注册" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_user_no_permission(async_client, user_token):
    """测试无权限创建用户"""
    token = await user_token
    headers = {"Authorization": f"Bearer {token}"}
    new_user = {
        "email": "newuser@test.com",
        "username": "newuser",
        "password": "newuser123",
        "roles": ["customer"]
    }
    
    response = await async_client.post(
        "/api/v1/users/",
        headers=headers,
        json=new_user
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "没有足够的权限" in response.json()["detail"]

@pytest.mark.asyncio
async def test_read_users(async_client, admin_token):
    """测试获取用户列表"""
    token = await admin_token
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await async_client.get(
        "/api/v1/users/",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # 验证返回的用户数据结构
    user = data[0]
    assert "id" in user
    assert "email" in user
    assert "username" in user
    assert "roles" in user

@pytest.mark.asyncio
async def test_read_users_no_permission(async_client, user_token):
    """测试无权限获取用户列表"""
    token = await user_token
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await async_client.get(
        "/api/v1/users/",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "没有足够的权限" in response.json()["detail"]

@pytest.mark.asyncio
async def test_read_user_me(async_client, user_token):
    """测试获取当前用户信息"""
    token = await user_token
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await async_client.get(
        "/api/v1/users/me",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["username"] == test_user["username"]
    assert "customer" in data["roles"]

@pytest.mark.asyncio
async def test_update_user_me(async_client, user_token):
    """测试更新当前用户信息"""
    token = await user_token
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await async_client.put(
        "/api/v1/users/me",
        headers=headers,
        json=test_user_update
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == test_user_update["username"]
    assert data["phone"] == test_user_update["phone"]

@pytest.mark.asyncio
async def test_read_user_by_id(async_client, admin_token, user_token):
    """测试根据ID获取用户信息"""
    # 先获取用户ID
    user_token_str = await user_token
    headers = {"Authorization": f"Bearer {user_token_str}"}
    me_response = await async_client.get(
        "/api/v1/users/me",
        headers=headers
    )
    user_id = me_response.json()["id"]
    
    # 使用管理员token获取该用户信息
    admin_token_str = await admin_token
    headers = {"Authorization": f"Bearer {admin_token_str}"}
    response = await async_client.get(
        f"/api/v1/users/{user_id}",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == test_user["email"]

@pytest.mark.asyncio
async def test_read_user_not_found(async_client, admin_token):
    """测试获取不存在的用户"""
    token = await admin_token
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await async_client.get(
        "/api/v1/users/nonexistent",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "用户不存在" in response.json()["detail"]

@pytest.mark.asyncio
async def test_update_user(async_client, admin_token, user_token):
    """测试管理员更新用户信息"""
    # 先获取用户ID
    user_token_str = await user_token
    headers = {"Authorization": f"Bearer {user_token_str}"}
    me_response = await async_client.get(
        "/api/v1/users/me",
        headers=headers
    )
    user_id = me_response.json()["id"]
    
    # 使用管理员token更新用户信息
    admin_token_str = await admin_token
    headers = {"Authorization": f"Bearer {admin_token_str}"}
    update_data = {
        "username": "admin_updated",
        "roles": ["customer", "consultant"]
    }
    
    response = await async_client.put(
        f"/api/v1/users/{user_id}",
        headers=headers,
        json=update_data
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == update_data["username"]
    assert set(data["roles"]) == set(update_data["roles"])

@pytest.mark.asyncio
async def test_update_user_no_permission(async_client, user_token):
    """测试无权限更新其他用户信息"""
    token = await user_token
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await async_client.put(
        "/api/v1/users/someuser",
        headers=headers,
        json=test_user_update
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "没有足够的权限" in response.json()["detail"]

@pytest.mark.asyncio
async def test_read_roles(async_client, admin_token):
    """测试获取所有角色"""
    token = await admin_token
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await async_client.get(
        "/api/v1/users/roles/all",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    # 验证是否包含基本角色
    role_names = [role["name"] for role in data]
    assert "admin" in role_names
    assert "customer" in role_names

@pytest.mark.asyncio
async def test_read_roles_no_permission(async_client, user_token):
    """测试无权限获取角色列表"""
    token = await user_token
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await async_client.get(
        "/api/v1/users/roles/all",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "没有足够的权限" in response.json()["detail"] 