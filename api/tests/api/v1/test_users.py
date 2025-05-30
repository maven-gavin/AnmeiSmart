import pytest
from fastapi import status
from sqlalchemy.orm import Session
from typing import Dict, Generator
from httpx import AsyncClient, ASGITransport
import pytest_asyncio
from fastapi.testclient import TestClient

from app.db.models.user import User, Role
from app.services import user_service
from app.core.security import create_access_token
from app.schemas.user import UserCreate, UserUpdate
from main import app

@pytest_asyncio.fixture
async def admin_token(db: Session, test_admin_data: Dict) -> str:
    """创建管理员用户并返回token"""
    admin_in = UserCreate(**test_admin_data)
    admin = await user_service.create(db, obj_in=admin_in)
    return create_access_token(admin.id)

@pytest_asyncio.fixture
async def user_token(db: Session, test_user_data: Dict) -> str:
    """创建普通用户并返回token"""
    user_in = UserCreate(**test_user_data)
    user = await user_service.create(db, obj_in=user_in)
    return create_access_token(user.id)

@pytest.mark.asyncio
async def test_create_user(async_client, admin_token):
    """测试创建用户接口"""
    headers = {"Authorization": f"Bearer {admin_token}"}
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
async def test_create_user_existing_email(async_client, admin_token, user_token, test_user_data):
    """测试创建已存在邮箱的用户"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    response = await async_client.post(
        "/api/v1/users/",
        headers=headers,
        json=test_user_data
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Email已被使用" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_user_no_permission(async_client, user_token):
    """测试无权限创建用户"""
    headers = {"Authorization": f"Bearer {user_token}"}
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
    headers = {"Authorization": f"Bearer {admin_token}"}
    
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
    headers = {"Authorization": f"Bearer {user_token}"}
    
    response = await async_client.get(
        "/api/v1/users/",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "没有足够的权限" in response.json()["detail"]

@pytest.mark.asyncio
async def test_read_user_me(async_client, user_token, test_user_data):
    """测试获取当前用户信息"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    response = await async_client.get(
        "/api/v1/users/me",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == test_user_data["email"]
    assert data["username"] == test_user_data["username"]
    assert "customer" in data["roles"]

@pytest.mark.asyncio
async def test_update_user_me(async_client, user_token, test_user_update_data):
    """测试更新当前用户信息"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    response = await async_client.put(
        "/api/v1/users/me",
        headers=headers,
        json=test_user_update_data
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["username"] == test_user_update_data["username"]
    assert data["phone"] == test_user_update_data["phone"]

@pytest.mark.asyncio
async def test_read_user_by_id(async_client, admin_token, user_token, test_user_data):
    """测试根据ID获取用户信息"""
    # 先获取用户ID
    headers = {"Authorization": f"Bearer {user_token}"}
    me_response = await async_client.get(
        "/api/v1/users/me",
        headers=headers
    )
    user_id = me_response.json()["id"]
    
    # 使用管理员token获取该用户信息
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get(
        f"/api/v1/users/{user_id}",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == user_id
    assert data["email"] == test_user_data["email"]

@pytest.mark.asyncio
async def test_read_user_not_found(async_client, admin_token):
    """测试获取不存在的用户"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
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
    headers = {"Authorization": f"Bearer {user_token}"}
    me_response = await async_client.get(
        "/api/v1/users/me",
        headers=headers
    )
    user_id = me_response.json()["id"]
    
    # 使用管理员token更新用户信息
    headers = {"Authorization": f"Bearer {admin_token}"}
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
async def test_update_user_no_permission(async_client, user_token, test_user_update_data):
    """测试无权限更新其他用户信息"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    response = await async_client.put(
        "/api/v1/users/someuser",
        headers=headers,
        json=test_user_update_data
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "没有足够的权限" in response.json()["detail"]

@pytest.mark.asyncio
async def test_read_roles(async_client, admin_token):
    """测试获取所有角色"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
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
    headers = {"Authorization": f"Bearer {user_token}"}
    
    response = await async_client.get(
        "/api/v1/users/roles/all",
        headers=headers
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "没有足够的权限" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_user_invalid_email(async_client, admin_token):
    """测试创建用户时使用无效的邮箱格式"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    invalid_user = {
        "email": "invalid_email",  # 无效的邮箱格式
        "username": "newuser",
        "password": "newuser123",
        "roles": ["customer"]
    }
    
    response = await async_client.post(
        "/api/v1/users/",
        headers=headers,
        json=invalid_user
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "email" in response.json()["detail"][0]["loc"]

@pytest.mark.asyncio
async def test_create_user_weak_password(async_client, admin_token):
    """测试创建用户时使用弱密码"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    weak_password_user = {
        "email": "newuser@test.com",
        "username": "newuser",
        "password": "123",  # 弱密码
        "roles": ["customer"]
    }
    
    response = await async_client.post(
        "/api/v1/users/",
        headers=headers,
        json=weak_password_user
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "password" in response.json()["detail"][0]["loc"]

@pytest.mark.asyncio
async def test_create_user_invalid_role(async_client, admin_token):
    """测试创建用户时使用无效的角色"""
    headers = {"Authorization": f"Bearer {admin_token}"}
    invalid_role_user = {
        "email": "newuser@test.com",
        "username": "newuser",
        "password": "newuser123",
        "roles": ["invalid_role"]  # 无效的角色
    }
    
    response = await async_client.post(
        "/api/v1/users/",
        headers=headers,
        json=invalid_role_user
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "无效的角色: invalid_role" in response.json()["detail"] 