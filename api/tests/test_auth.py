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