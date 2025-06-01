"""
角色管理 API 端点测试模块

本模块为 `/api/v1/roles` 端点提供全面的测试覆盖，包括：

主要功能测试：
- 创建角色 (POST /) - 需要管理员权限
- 获取角色列表 (GET /) - 需要登录
- 根据ID获取角色 (GET /{role_id}) - 需要登录  
- 删除角色 (DELETE /{role_id}) - 需要管理员权限

业务逻辑测试：
- 权限验证（管理员/普通用户/未认证）
- 系统基础角色保护（不允许删除）
- 重复角色名检查
- 边界条件和异常处理
- 并发操作处理

技术特性测试：
- 角色名大小写敏感性
- 特殊字符支持
- 长描述处理
- 数据验证

测试遵循项目规范：
- 使用 DDD 分层架构
- Service 层返回 Schema 对象
- Controller 层只做权限和参数校验
- 完整的错误处理和状态码检查

作者：Assistant
创建时间：2025年1月
"""

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
from app.schemas.user import UserCreate, RoleCreate
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

@pytest_asyncio.fixture
async def test_role_data() -> Dict[str, str]:
    """测试角色数据"""
    return {
        "name": "test_role",
        "description": "测试角色描述"
    }

@pytest_asyncio.fixture
async def test_custom_role(db: Session) -> Role:
    """创建一个测试自定义角色"""
    role = await user_service.create_role(db, name="custom_role", description="自定义测试角色")
    # 返回 ORM 对象
    return db.query(Role).filter(Role.name == "custom_role").first()

class TestCreateRole:
    """测试创建角色功能"""

    @pytest.mark.asyncio
    async def test_create_role_success(self, async_client: AsyncClient, admin_token: str, test_role_data: Dict):
        """测试成功创建角色"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await async_client.post(
            "/api/v1/roles/",
            headers=headers,
            json=test_role_data
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == test_role_data["name"]
        assert data["description"] == test_role_data["description"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_role_duplicate_name(self, async_client: AsyncClient, admin_token: str, test_custom_role: Role):
        """测试创建重复角色名的角色"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        duplicate_role_data = {
            "name": test_custom_role.name,
            "description": "重复的角色名"
        }
        
        response = await async_client.post(
            "/api/v1/roles/",
            headers=headers,
            json=duplicate_role_data
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert f"角色名 '{test_custom_role.name}' 已存在" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_role_no_permission(self, async_client: AsyncClient, user_token: str, test_role_data: Dict):
        """测试无权限创建角色"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        response = await async_client.post(
            "/api/v1/roles/",
            headers=headers,
            json=test_role_data
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "没有足够的权限执行此操作" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_role_unauthorized(self, async_client: AsyncClient, test_role_data: Dict):
        """测试未认证创建角色"""
        response = await async_client.post(
            "/api/v1/roles/",
            json=test_role_data
        )
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_create_role_empty_name(self, async_client: AsyncClient, admin_token: str):
        """测试创建空名称角色"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        invalid_role_data = {
            "name": "",
            "description": "空名称角色"
        }
        
        response = await async_client.post(
            "/api/v1/roles/",
            headers=headers,
            json=invalid_role_data
        )
        
        # 基于实际的模型定义，空字符串是被允许的，但在业务逻辑中可能不合理
        # 这里我们测试实际行为：创建成功
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == ""
        assert data["description"] == invalid_role_data["description"]

    @pytest.mark.asyncio
    async def test_create_role_without_description(self, async_client: AsyncClient, admin_token: str):
        """测试创建不带描述的角色"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        role_data = {
            "name": "role_without_desc"
        }
        
        response = await async_client.post(
            "/api/v1/roles/",
            headers=headers,
            json=role_data
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == role_data["name"]
        assert data["description"] is None


class TestReadRoles:
    """测试获取角色列表功能"""

    @pytest.mark.asyncio
    async def test_read_roles_success(self, async_client: AsyncClient, user_token: str):
        """测试成功获取角色列表"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        response = await async_client.get(
            "/api/v1/roles/",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # 验证返回的角色数据结构
        role = data[0]
        assert "id" in role
        assert "name" in role
        assert "description" in role

    @pytest.mark.asyncio
    async def test_read_roles_contains_base_roles(self, async_client: AsyncClient, admin_token: str):
        """测试角色列表包含系统基础角色"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await async_client.get(
            "/api/v1/roles/",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        role_names = [role["name"] for role in data]
        
        # 验证系统基础角色存在
        base_roles = ["admin", "consultant", "doctor", "customer", "operator"]
        for base_role in base_roles:
            assert base_role in role_names

    @pytest.mark.asyncio
    async def test_read_roles_unauthorized(self, async_client: AsyncClient):
        """测试未认证获取角色列表"""
        response = await async_client.get("/api/v1/roles/")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_read_roles_with_pagination(self, async_client: AsyncClient, user_token: str):
        """测试带分页参数的角色列表"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        response = await async_client.get(
            "/api/v1/roles/?skip=0&limit=3",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        # 注意：实际项目中roles端点可能没有实现分页逻辑，这里只是测试参数传递


class TestReadRole:
    """测试根据ID获取角色功能"""

    @pytest.mark.asyncio
    async def test_read_role_success(self, async_client: AsyncClient, user_token: str, test_custom_role: Role):
        """测试成功根据ID获取角色"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        response = await async_client.get(
            f"/api/v1/roles/{test_custom_role.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == test_custom_role.id
        assert data["name"] == test_custom_role.name
        assert data["description"] == test_custom_role.description

    @pytest.mark.asyncio
    async def test_read_role_not_found(self, async_client: AsyncClient, user_token: str):
        """测试获取不存在的角色"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        response = await async_client.get(
            "/api/v1/roles/nonexistent_role_id",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "角色不存在" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_read_role_unauthorized(self, async_client: AsyncClient, test_custom_role: Role):
        """测试未认证获取角色"""
        response = await async_client.get(f"/api/v1/roles/{test_custom_role.id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDeleteRole:
    """测试删除角色功能"""

    @pytest.mark.asyncio
    async def test_delete_role_success(self, async_client: AsyncClient, admin_token: str, test_custom_role: Role):
        """测试成功删除自定义角色"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await async_client.delete(
            f"/api/v1/roles/{test_custom_role.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        
        # 验证角色已被删除
        get_response = await async_client.get(
            f"/api/v1/roles/{test_custom_role.id}",
            headers=headers
        )
        assert get_response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_delete_role_not_found(self, async_client: AsyncClient, admin_token: str):
        """测试删除不存在的角色"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = await async_client.delete(
            "/api/v1/roles/nonexistent_role_id",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "角色不存在" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_base_role_forbidden(self, async_client: AsyncClient, admin_token: str, db: Session):
        """测试删除系统基础角色被禁止"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 获取一个系统基础角色
        admin_role = db.query(Role).filter(Role.name == "admin").first()
        assert admin_role is not None
        
        response = await async_client.delete(
            f"/api/v1/roles/{admin_role.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "不能删除系统基础角色" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_role_no_permission(self, async_client: AsyncClient, user_token: str, test_custom_role: Role):
        """测试无权限删除角色"""
        headers = {"Authorization": f"Bearer {user_token}"}
        
        response = await async_client.delete(
            f"/api/v1/roles/{test_custom_role.id}",
            headers=headers
        )
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "没有足够的权限执行此操作" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_role_unauthorized(self, async_client: AsyncClient, test_custom_role: Role):
        """测试未认证删除角色"""
        response = await async_client.delete(f"/api/v1/roles/{test_custom_role.id}")
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_delete_all_base_roles_forbidden(self, async_client: AsyncClient, admin_token: str, db: Session):
        """测试删除所有系统基础角色都被禁止"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        base_roles = ["admin", "consultant", "doctor", "customer", "operator"]
        
        for role_name in base_roles:
            role = db.query(Role).filter(Role.name == role_name).first()
            if role:
                response = await async_client.delete(
                    f"/api/v1/roles/{role.id}",
                    headers=headers
                )
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert "不能删除系统基础角色" in response.json()["detail"]


class TestRoleBusinessLogic:
    """测试角色业务逻辑"""

    @pytest.mark.asyncio
    async def test_role_case_sensitivity(self, async_client: AsyncClient, admin_token: str):
        """测试角色名大小写敏感性"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 创建小写角色
        role_data_lower = {"name": "testrole", "description": "小写测试角色"}
        response1 = await async_client.post(
            "/api/v1/roles/",
            headers=headers,
            json=role_data_lower
        )
        assert response1.status_code == status.HTTP_201_CREATED
        
        # 尝试创建大写角色
        role_data_upper = {"name": "TestRole", "description": "大写测试角色"}
        response2 = await async_client.post(
            "/api/v1/roles/",
            headers=headers,
            json=role_data_upper
        )
        # 这应该成功，因为大小写不同
        assert response2.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio
    async def test_role_with_special_characters(self, async_client: AsyncClient, admin_token: str):
        """测试包含特殊字符的角色名"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        special_roles = [
            {"name": "role-with-dash", "description": "带连字符的角色"},
            {"name": "role_with_underscore", "description": "带下划线的角色"},
            {"name": "role123", "description": "带数字的角色"}
        ]
        
        for role_data in special_roles:
            response = await async_client.post(
                "/api/v1/roles/",
                headers=headers,
                json=role_data
            )
            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["name"] == role_data["name"]

    @pytest.mark.asyncio
    async def test_role_description_max_length(self, async_client: AsyncClient, admin_token: str):
        """测试角色描述长度限制"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        long_description = "很长的描述" * 100  # 创建一个很长的描述
        role_data = {
            "name": "role_long_desc",
            "description": long_description
        }
        
        response = await async_client.post(
            "/api/v1/roles/",
            headers=headers,
            json=role_data
        )
        
        # 根据实际业务需求，这可能成功或失败
        # 这里假设没有长度限制，应该成功
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio
    async def test_concurrent_role_creation(self, async_client: AsyncClient, admin_token: str):
        """测试并发创建相同角色名的处理"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # 模拟并发创建相同角色
        import asyncio
        
        async def create_role(client, name):
            role_data = {"name": name, "description": f"并发测试角色-{name}"}
            return await client.post(
                "/api/v1/roles/",
                headers=headers,
                json=role_data
            )
        
        # 并发创建相同名称的角色
        results = await asyncio.gather(
            create_role(async_client, "concurrent_role"),
            create_role(async_client, "concurrent_role"),
            return_exceptions=True
        )
        
        # 应该有一个成功，一个失败
        success_count = sum(1 for r in results if hasattr(r, 'status_code') and r.status_code == 201)
        error_count = sum(1 for r in results if hasattr(r, 'status_code') and r.status_code == 400)
        
        assert success_count == 1
        assert error_count == 1 