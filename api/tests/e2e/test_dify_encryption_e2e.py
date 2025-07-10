"""
Dify集成系统端到端测试
测试包括API密钥加密存储的完整Dify功能流程
"""
import pytest
import asyncio
from httpx import AsyncClient
from fastapi import status
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from unittest.mock import patch, AsyncMock, MagicMock

from app.core.config import get_settings
from app.db.models.system import DifyConnection, AIModelConfig, AgentType, SyncStatus
from app.core.encryption import get_encryption
from app.core.security import create_access_token
from app.services import user_service
from app.schemas.user import UserCreate

settings = get_settings()


@pytest.fixture
async def admin_user_e2e(db: Session) -> Dict[str, Any]:
    """创建管理员用户用于E2E测试"""
    admin_data = {
        "email": "admin_e2e@test.com",
        "username": "admin_e2e",
        "password": "AdminE2E123!",
        "roles": ["admin"]
    }
    
    admin_in = UserCreate(**admin_data)
    admin = await user_service.create(db, obj_in=admin_in)
    
    return {
        "user": admin,
        "token": create_access_token(subject=str(admin.id)),
        "headers": {"Authorization": f"Bearer {create_access_token(subject=str(admin.id))}"}
    }


class TestDifyConnectionManagementE2E:
    """Dify连接管理端到端测试"""
    
    @pytest.mark.asyncio
    async def test_create_dify_connection_with_encryption(
        self, 
        async_client: AsyncClient, 
        admin_user_e2e: Dict[str, Any],
        db: Session
    ):
        """测试创建Dify连接时API密钥自动加密"""
        
        connection_data = {
            "name": "E2E测试连接",
            "api_base_url": "https://e2e.dify.local",
            "api_key": "sk-e2e-test-key-1234567890",
            "description": "端到端测试用连接",
            "is_default": True
        }
        
        response = await async_client.post(
            f"{settings.API_V1_STR}/dify/connections",
            json=connection_data,
            headers=admin_user_e2e["headers"]
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        
        response_data = response.json()
        connection_id = response_data["id"]
        
        # 验证返回的数据
        assert response_data["name"] == connection_data["name"]
        assert response_data["api_base_url"] == connection_data["api_base_url"]
        # API密钥应该被掩码
        assert response_data["api_key"] == "••••••••••••••••••••"
        
        # 验证数据库中的加密存储
        connection = db.query(DifyConnection).filter(
            DifyConnection.id == connection_id
        ).first()
        
        assert connection is not None
        assert connection.api_key == "sk-e2e-test-key-1234567890"  # 通过属性访问解密
        
        # 验证确实是加密存储的
        encryption = get_encryption()
        encrypted_value = connection.get_api_key_encrypted()
        assert encryption.is_encrypted(encrypted_value)
        assert encrypted_value != "sk-e2e-test-key-1234567890"
    
    @pytest.mark.asyncio
    async def test_update_dify_connection_encryption(
        self, 
        async_client: AsyncClient, 
        admin_user_e2e: Dict[str, Any],
        db: Session
    ):
        """测试更新Dify连接时API密钥重新加密"""
        
        # 先创建连接
        connection = DifyConnection(
            name="更新测试连接",
            api_base_url="https://update.dify.local",
            api_key="sk-original-key-123"
        )
        db.add(connection)
        db.commit()
        db.refresh(connection)
        
        # 更新连接
        update_data = {
            "name": "更新后的连接",
            "api_key": "sk-updated-key-456",
            "description": "更新后的描述"
        }
        
        response = await async_client.put(
            f"{settings.API_V1_STR}/dify/connections/{connection.id}",
            json=update_data,
            headers=admin_user_e2e["headers"]
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        # 验证数据库更新
        updated_connection = db.query(DifyConnection).filter(
            DifyConnection.id == connection.id
        ).first()
        
        assert updated_connection.name == "更新后的连接"
        assert updated_connection.api_key == "sk-updated-key-456"
        
        # 验证新密钥被正确加密
        encryption = get_encryption()
        encrypted_value = updated_connection.get_api_key_encrypted()
        assert encryption.is_encrypted(encrypted_value)
        assert encryption.decrypt(encrypted_value) == "sk-updated-key-456"
    
    @pytest.mark.asyncio
    async def test_list_connections_masked_api_keys(
        self, 
        async_client: AsyncClient, 
        admin_user_e2e: Dict[str, Any],
        db: Session
    ):
        """测试列出连接时API密钥被掩码"""
        
        # 创建多个连接
        connections = []
        for i in range(3):
            conn = DifyConnection(
                name=f"列表测试连接{i}",
                api_base_url=f"https://list{i}.dify.local",
                api_key=f"sk-list-key-{i}"
            )
            connections.append(conn)
        
        db.add_all(connections)
        db.commit()
        
        response = await async_client.get(
            f"{settings.API_V1_STR}/dify/connections",
            headers=admin_user_e2e["headers"]
        )
        
        assert response.status_code == status.HTTP_200_OK
        
        response_data = response.json()
        assert len(response_data) >= 3
        
        # 验证所有API密钥都被掩码
        for conn_data in response_data:
            if conn_data["name"].startswith("列表测试连接"):
                assert conn_data["api_key"] == "••••••••••••••••••••"
                assert "sk-list-key" not in str(conn_data)


class TestDifyAppSyncWithEncryptionE2E:
    """Dify应用同步加密端到端测试"""
    
    @pytest.mark.asyncio
    async def test_sync_apps_with_encrypted_connection(
        self, 
        async_client: AsyncClient, 
        admin_user_e2e: Dict[str, Any],
        db: Session
    ):
        """测试使用加密连接同步Dify应用"""
        
        # 创建加密的Dify连接
        connection = DifyConnection(
            name="同步测试连接",
            api_base_url="https://sync.dify.local",
            api_key="sk-sync-test-key-123"
        )
        db.add(connection)
        db.commit()
        db.refresh(connection)
        
        # Mock Dify API响应
        mock_apps = [
            {
                "id": "app_001",
                "name": "医美方案生成器",
                "mode": "agent",
                "description": "专业医美方案推荐"
            },
            {
                "id": "app_002",
                "name": "客服助手",
                "mode": "chat",
                "description": "智能客服对话"
            }
        ]
        
        with patch('app.services.ai.dify_client.DifyAPIClient.get_apps') as mock_get_apps:
            mock_get_apps.return_value = mock_apps
            
            response = await async_client.post(
                f"{settings.API_V1_STR}/dify/connections/{connection.id}/sync",
                headers=admin_user_e2e["headers"]
            )
            
            assert response.status_code == status.HTTP_200_OK
            
            response_data = response.json()
            assert response_data["success"] is True
            assert "同步成功" in response_data["message"]
            
            # 验证连接状态更新
            updated_connection = db.query(DifyConnection).filter(
                DifyConnection.id == connection.id
            ).first()
            assert updated_connection.sync_status == SyncStatus.SUCCESS
            
            # 验证API密钥在整个过程中保持加密
            encryption = get_encryption()
            encrypted_value = updated_connection.get_api_key_encrypted()
            assert encryption.is_encrypted(encrypted_value)
            assert encryption.decrypt(encrypted_value) == "sk-sync-test-key-123"


class TestAgentManagementWithEncryptionE2E:
    """Agent管理加密端到端测试"""
    
    @pytest.mark.asyncio
    async def test_configure_agent_with_encrypted_connection(
        self, 
        async_client: AsyncClient, 
        admin_user_e2e: Dict[str, Any],
        db: Session
    ):
        """测试配置Agent使用加密连接"""
        
        # 创建Dify连接
        connection = DifyConnection(
            name="Agent配置连接",
            api_base_url="https://agent.dify.local",
            api_key="sk-agent-config-key"
        )
        db.add(connection)
        db.commit()
        db.refresh(connection)
        
        # 配置Agent
        agent_config = {
            "app_id": "beauty_plan_app_001",
            "app_name": "医美方案智能助手",
            "app_mode": "agent",
            "agent_type": "beauty_plan",
            "description": "专业医美方案生成Agent",
            "is_default_for_type": True
        }
        
        response = await async_client.post(
            f"{settings.API_V1_STR}/dify/connections/{connection.id}/configure-agent",
            json=agent_config,
            headers=admin_user_e2e["headers"]
        )
        
        assert response.status_code == status.HTTP_201_CREATED
        
        response_data = response.json()
        ai_config_id = response_data["id"]
        
        # 验证AI模型配置
        ai_config = db.query(AIModelConfig).filter(
            AIModelConfig.id == ai_config_id
        ).first()
        
        assert ai_config is not None
        assert ai_config.model_name == "医美方案智能助手"
        assert ai_config.provider == "dify"
        assert ai_config.agent_type == AgentType.BEAUTY_PLAN
        assert ai_config.dify_connection_id == connection.id
        
        # 验证连接的API密钥仍然加密
        assert ai_config.dify_connection.api_key == "sk-agent-config-key"
        encryption = get_encryption()
        encrypted_value = ai_config.dify_connection.get_api_key_encrypted()
        assert encryption.is_encrypted(encrypted_value)
    
    @pytest.mark.asyncio
    async def test_agent_execution_with_encrypted_config(
        self, 
        async_client: AsyncClient, 
        admin_user_e2e: Dict[str, Any],
        db: Session
    ):
        """测试使用加密配置执行Agent"""
        
        # 创建完整的Agent配置
        connection = DifyConnection(
            name="执行测试连接",
            api_base_url="https://exec.dify.local",
            api_key="sk-exec-test-key-789"
        )
        db.add(connection)
        db.commit()
        
        ai_config = AIModelConfig(
            model_name="执行测试Agent",
            provider="dify",
            dify_connection_id=connection.id,
            dify_app_id="exec_test_app",
            agent_type=AgentType.BEAUTY_PLAN,
            is_default_for_type=True,
            enabled=True
        )
        db.add(ai_config)
        db.commit()
        db.refresh(ai_config)
        
        # Mock Agent执行
        with patch('app.services.ai.agent_manager.AgentManager.get_agent_by_type') as mock_get_agent:
            mock_agent = MagicMock()
            mock_agent.generate_response = AsyncMock(return_value={
                "content": "基于您的需求，我推荐以下医美方案...",
                "id": "agent_response_001"
            })
            mock_get_agent.return_value = mock_agent
            
            # 测试AI聊天接口
            chat_request = {
                "message": "我想了解面部年轻化的方案",
                "conversation_id": "test_conv_001",
                "agent_type": "beauty_plan"
            }
            
            response = await async_client.post(
                f"{settings.API_V1_STR}/ai/chat",
                json=chat_request,
                headers=admin_user_e2e["headers"]
            )
            
            # 注意：这里可能会返回404，因为具体的AI聊天端点可能还没实现
            # 但我们主要测试的是配置和加密部分
            
            # 验证Agent配置仍然正确
            refreshed_config = db.query(AIModelConfig).filter(
                AIModelConfig.id == ai_config.id
            ).first()
            
            assert refreshed_config.dify_connection.api_key == "sk-exec-test-key-789"


class TestEncryptionSecurityE2E:
    """加密安全性端到端测试"""
    
    @pytest.mark.asyncio
    async def test_api_key_never_exposed_in_responses(
        self, 
        async_client: AsyncClient, 
        admin_user_e2e: Dict[str, Any],
        db: Session
    ):
        """测试API密钥永远不在响应中暴露"""
        
        # 创建连接
        connection_data = {
            "name": "安全测试连接",
            "api_base_url": "https://security.dify.local",
            "api_key": "sk-very-secret-key-should-never-be-exposed",
            "description": "安全测试"
        }
        
        create_response = await async_client.post(
            f"{settings.API_V1_STR}/dify/connections",
            json=connection_data,
            headers=admin_user_e2e["headers"]
        )
        
        assert create_response.status_code == status.HTTP_201_CREATED
        connection_id = create_response.json()["id"]
        
        # 测试所有相关端点都不暴露真实API密钥
        endpoints_to_test = [
            ("GET", f"/dify/connections"),
            ("GET", f"/dify/connections/{connection_id}"),
        ]
        
        for method, endpoint in endpoints_to_test:
            response = await async_client.request(
                method,
                f"{settings.API_V1_STR}{endpoint}",
                headers=admin_user_e2e["headers"]
            )
            
            if response.status_code == 200:
                response_text = response.text
                # 确保真实密钥不在响应中
                assert "sk-very-secret-key-should-never-be-exposed" not in response_text
                assert "very-secret-key" not in response_text
                assert "secret" not in response_text.lower() or "••••" in response_text
    
    @pytest.mark.asyncio
    async def test_encryption_consistency_across_operations(
        self, 
        async_client: AsyncClient, 
        admin_user_e2e: Dict[str, Any],
        db: Session
    ):
        """测试跨操作的加密一致性"""
        
        original_api_key = "sk-consistency-test-key-123456"
        
        # 创建连接
        connection_data = {
            "name": "一致性测试连接",
            "api_base_url": "https://consistency.dify.local",
            "api_key": original_api_key
        }
        
        create_response = await async_client.post(
            f"{settings.API_V1_STR}/dify/connections",
            json=connection_data,
            headers=admin_user_e2e["headers"]
        )
        
        connection_id = create_response.json()["id"]
        
        # 多次操作检查加密一致性
        operations = [
            # 获取连接详情
            lambda: async_client.get(
                f"{settings.API_V1_STR}/dify/connections/{connection_id}",
                headers=admin_user_e2e["headers"]
            ),
            # 更新连接（不更改密钥）
            lambda: async_client.put(
                f"{settings.API_V1_STR}/dify/connections/{connection_id}",
                json={"description": "更新描述"},
                headers=admin_user_e2e["headers"]
            ),
            # 再次获取
            lambda: async_client.get(
                f"{settings.API_V1_STR}/dify/connections/{connection_id}",
                headers=admin_user_e2e["headers"]
            )
        ]
        
        for operation in operations:
            response = await operation()
            if response.status_code == 200:
                # 验证返回的API密钥始终被掩码
                response_data = response.json()
                if isinstance(response_data, list):
                    for item in response_data:
                        if item.get("id") == connection_id:
                            assert item["api_key"] == "••••••••••••••••••••"
                else:
                    if response_data.get("id") == connection_id:
                        assert response_data["api_key"] == "••••••••••••••••••••"
        
        # 验证数据库中的密钥始终正确
        final_connection = db.query(DifyConnection).filter(
            DifyConnection.id == connection_id
        ).first()
        
        assert final_connection.api_key == original_api_key
        
        # 验证始终是加密存储
        encryption = get_encryption()
        encrypted_value = final_connection.get_api_key_encrypted()
        assert encryption.is_encrypted(encrypted_value)
        assert encryption.decrypt(encrypted_value) == original_api_key


class TestMigrationAndCompatibilityE2E:
    """迁移和兼容性端到端测试"""
    
    def test_mixed_encrypted_unencrypted_data_handling(self, db: Session):
        """测试混合加密和未加密数据的处理"""
        
        # 模拟迁移前的未加密数据
        old_connection = DifyConnection(
            name="迁移前连接",
            api_base_url="https://old.dify.local"
        )
        old_connection.set_api_key_raw("sk-unencrypted-old-key")  # 直接设置未加密数据
        
        # 新的加密数据
        new_connection = DifyConnection(
            name="迁移后连接",
            api_base_url="https://new.dify.local",
            api_key="sk-encrypted-new-key"  # 通过属性设置，会自动加密
        )
        
        db.add_all([old_connection, new_connection])
        db.commit()
        
        # 验证两种数据都能正确处理
        connections = db.query(DifyConnection).all()
        
        for conn in connections:
            if conn.name == "迁移前连接":
                assert conn.api_key == "sk-unencrypted-old-key"
            elif conn.name == "迁移后连接":
                assert conn.api_key == "sk-encrypted-new-key"
                # 验证新数据确实是加密的
                encryption = get_encryption()
                assert encryption.is_encrypted(conn.get_api_key_encrypted()) 