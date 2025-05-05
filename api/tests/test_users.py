from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest
from typing import Dict, Generator

from app.main import app
from app.db.base import Base, engine, get_db
from app.core.config import get_settings
from app.models.user import UserCreate

settings = get_settings()

# 设置测试数据库
Base.metadata.create_all(bind=engine)

def override_get_db() -> Generator[Session, None, None]:
    """覆盖数据库依赖"""
    try:
        db = Session(engine)
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

def test_create_user(client: TestClient) -> None:
    """测试创建用户"""
    data = {
        "email": "new_user@example.com",
        "username": "newuser",
        "password": "testpassword123"
    }
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        json=data,
    )
    assert response.status_code == 201
    content = response.json()
    assert content["email"] == data["email"]
    assert content["username"] == data["username"]
    assert "id" in content
    assert "password" not in content

def test_create_user_existing_email(client: TestClient, test_user: dict) -> None:
    """测试创建已存在邮箱的用户"""
    data = {
        "email": test_user["email"],
        "username": "testuser2",
        "password": "testpassword123"
    }
    response = client.post(
        f"{settings.API_V1_STR}/users/",
        json=data,
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "该邮箱已被注册"

def test_read_user_me(client: TestClient, test_user: dict) -> None:
    """测试获取当前用户信息"""
    # 先登录获取token
    login_data = {
        "username": test_user["email"],
        "password": test_user["password"]
    }
    login_response = client.post(
        f"{settings.API_V1_STR}/auth/login",
        data=login_data
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # 获取用户信息
    response = client.get(
        f"{settings.API_V1_STR}/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    content = response.json()
    assert content["email"] == test_user["email"]
    assert content["username"] == test_user["username"] 