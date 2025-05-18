from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest
from typing import Dict, Generator
import sys
import os

# 将项目根目录添加到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from app.db.base import get_db
from app.core.config import get_settings
from app.schemas.user import UserCreate

settings = get_settings()

def test_create_user(client: TestClient, get_token: str) -> None:
    """测试创建用户"""
    token = get_token
    data = {
        "email": "new_user3@example.com",
        "username": "newuser3",
        "password": "testpassword123"
    }
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
    content = response.json()
    assert content["email"] == data["email"]
    assert content["username"] == data["username"]
    assert "id" in content
    assert "password" not in content

def test_create_user_existing_email(client: TestClient, test_user: dict, get_token: str) -> None:
    """测试创建已存在邮箱的用户"""
    token = get_token
    data = {
        "email": test_user["email"],
        "username": "testuser3",
        "password": "testpassword123"
    }
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "该邮箱已被注册"

def test_read_user_me(client: TestClient, test_user: dict, get_token: str) -> None:
    """测试获取当前用户信息"""
    token = get_token
    
    # 获取用户信息
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    content = response.json()
    assert content["email"] == test_user["email"]
    assert content["username"] == test_user["username"] 