import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from typing import Dict, List

from app.core.config import get_settings

settings = get_settings()

def test_login(client: TestClient, test_user: Dict[str, str]):
    """测试登录功能是否正常"""
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"],
    }
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data,
    )
    
    assert response.status_code == 200
    
    tokens = response.json()
    assert "access_token" in tokens
    assert tokens["token_type"] == "bearer"

def test_login_wrong_password(client: TestClient, test_user: dict) -> None:
    """测试密码错误"""
    login_data = {
        "username": test_user["email"],
        "password": "wrongpassword"
    }
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "邮箱或密码错误"

def test_login_nonexistent_user(client: TestClient) -> None:
    """测试不存在的用户"""
    login_data = {
        "username": "nonexistent@example.com",
        "password": "testpassword123"
    }
    response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data
    )
    
    assert response.status_code == 401
    assert response.json()["detail"] == "邮箱或密码错误"

def test_register_success(client: TestClient):
    """测试注册新用户"""
    user_data = {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "12345678",
        "roles": ["customer"]
    }
    response = client.post(f"{settings.API_V1_STR}/auth/register", json=user_data)
    assert response.status_code == 200 or response.status_code == 201

def test_register_duplicate_email(client: TestClient, test_user: dict):
    """测试重复注册"""
    user_data = {
        "email": test_user["email"],
        "username": "newuser",
        "password": "12345678",
        "roles": ["customer"]
    }
    response = client.post(f"{settings.API_V1_STR}/auth/register", json=user_data)
    assert response.status_code == 400

def test_refresh_token(client: TestClient, test_user: dict):
    """测试刷新token"""
    # 登录获取token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    refresh_token = login_resp.json()["refresh_token"]
    # 刷新token
    resp = client.post(f"{settings.API_V1_STR}/auth/refresh-token", json={"token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
    assert resp.json()["token_type"] == "bearer"

def test_refresh_token_invalid(client: TestClient):
    """测试无效token刷新"""
    resp = client.post(f"{settings.API_V1_STR}/auth/refresh-token", json={"token": "invalidtoken"})
    assert resp.status_code == 401

def test_get_me(client: TestClient, test_user: dict):
    """测试获取当前用户信息"""
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    resp = client.get(f"{settings.API_V1_STR}/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

def test_update_me(client: TestClient, test_user: dict):
    """测试更新当前用户信息"""
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    update_data = {"nickname": "新昵称"}
    resp = client.put(f"{settings.API_V1_STR}/auth/me", json=update_data, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

def test_get_roles(client: TestClient, test_user: dict):
    """测试获取用户所有角色"""
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    resp = client.get(f"{settings.API_V1_STR}/auth/roles", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)

def test_switch_role(client: TestClient, test_user: dict):
    """测试切换角色"""
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_resp = client.post(f"{settings.API_V1_STR}/auth/login", data=login_data)
    token = login_resp.json()["access_token"]
    # 假设test_user有customer角色
    switch_data = {"role": "customer"}
    resp = client.post(f"{settings.API_V1_STR}/auth/switch-role", json=switch_data, headers={"Authorization": f"Bearer {token}"})
    # 角色存在时应为200，否则403
    assert resp.status_code in (200, 403) 