import pytest
from fastapi import status
from sqlalchemy.orm import Session
from typing import Dict, Generator
from httpx import AsyncClient, ASGITransport
import pytest_asyncio
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch
import uuid

from app.db.models.user import User, Role
from app.db.models.chat import Conversation, Message
from app.services import user_service
from app.core.security import create_access_token
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.ai import AIChatRequest, AIChatResponse
from main import app

def unique_email(base_email: str) -> str:
    """生成唯一邮箱地址"""
    return f"test_{uuid.uuid4().hex[:8]}_{base_email}"

@pytest_asyncio.fixture
async def admin_token(db: Session, test_admin_data: Dict) -> str:
    """创建管理员用户并返回token"""
    admin_data = test_admin_data.copy()
    admin_data["email"] = unique_email(admin_data["email"])
    admin_in = UserCreate(**admin_data)
    admin = await user_service.create(db, obj_in=admin_in)
    return create_access_token(admin.id)

@pytest_asyncio.fixture
async def user_token(db: Session, test_user_data: Dict) -> str:
    """创建普通用户并返回token"""
    user_data = test_user_data.copy()
    user_data["email"] = unique_email(user_data["email"])
    user_in = UserCreate(**user_data)
    user = await user_service.create(db, obj_in=user_in)
    return create_access_token(user.id)

@pytest_asyncio.fixture
async def test_conversation(db: Session, user_token: str) -> str:
    """创建测试会话，返回会话ID"""
    # 直接返回会话ID，在测试中mock会话存在
    return "test_conv_001"

@pytest.mark.asyncio
async def test_ai_chat_success(async_client, user_token, test_conversation):
    """测试AI聊天成功场景"""
    headers = {"Authorization": f"Bearer {user_token}"}
    chat_request = {
        "conversation_id": test_conversation,
        "content": "你好，我想了解一下医美项目",
        "type": "text"
    }
    
    # Mock AI service response
    with patch("app.api.v1.endpoints.ai.get_ai_service") as mock_ai_service:
        mock_service = Mock()
        mock_service.get_response = AsyncMock(return_value={
            "content": "您好！我是安美智享的AI医美顾问，很高兴为您服务。请问您想了解哪类医美项目呢？",
            "timestamp": datetime.now().isoformat()
        })
        mock_ai_service.return_value = mock_service
        
        # Mock chat service
        with patch("app.api.v1.endpoints.ai.ChatService") as mock_chat_service:
            mock_chat = Mock()
            mock_chat.get_conversation_by_id.return_value = Mock(id=test_conversation)
            mock_chat.send_message = AsyncMock()
            mock_chat.send_message.side_effect = [
                # User message
                Mock(id="msg_user_001", content=chat_request["content"], timestamp=datetime.now()),
                # AI message  
                Mock(id="msg_ai_001", content="您好！我是安美智享的AI医美顾问...", 
                     timestamp=datetime.now(), type="text")
            ]
            mock_chat.get_conversation_messages.return_value = []
            mock_chat_service.return_value = mock_chat
            
            response = await async_client.post(
                "/api/v1/ai/chat",
                headers=headers,
                json=chat_request
            )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["content"] == "您好！我是安美智享的AI医美顾问..."
    assert data["conversation_id"] == chat_request["conversation_id"]
    assert data["type"] == "text"
    assert "sender" in data
    assert data["sender"]["type"] == "ai"

@pytest.mark.asyncio
async def test_ai_chat_conversation_not_found(async_client, user_token):
    """测试AI聊天会话不存在"""
    headers = {"Authorization": f"Bearer {user_token}"}
    chat_request = {
        "conversation_id": "nonexistent_conv",
        "content": "你好",
        "type": "text"
    }
    
    with patch("app.api.v1.endpoints.ai.ChatService") as mock_chat_service:
        mock_chat = Mock()
        mock_chat.get_conversation_by_id.return_value = None
        mock_chat_service.return_value = mock_chat
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=chat_request
        )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "会话不存在或无权访问" in response.json()["detail"]

@pytest.mark.asyncio
async def test_ai_chat_unauthorized(async_client):
    """测试未登录用户访问AI聊天"""
    chat_request = {
        "conversation_id": "test_conv_001", 
        "content": "你好",
        "type": "text"
    }
    
    response = await async_client.post(
        "/api/v1/ai/chat",
        json=chat_request
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_ai_chat_invalid_request(async_client, user_token):
    """测试AI聊天无效请求参数"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # 缺少必要字段
    invalid_request = {
        "conversation_id": "test_conv_001"
        # 缺少 content 字段
    }
    
    response = await async_client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json=invalid_request
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio 
async def test_ai_chat_service_error(async_client, user_token, test_conversation):
    """测试AI服务异常情况"""
    headers = {"Authorization": f"Bearer {user_token}"}
    chat_request = {
        "conversation_id": test_conversation,
        "content": "你好",
        "type": "text"
    }
    
    with patch("app.api.v1.endpoints.ai.ChatService") as mock_chat_service:
        mock_chat = Mock()
        mock_chat.get_conversation_by_id.return_value = Mock(id=test_conversation)
        mock_chat.send_message = AsyncMock(return_value=Mock(id="msg_001", content="你好", timestamp=datetime.now()))
        mock_chat.get_conversation_messages.return_value = []
        mock_chat_service.return_value = mock_chat
        
        # Mock AI service to raise exception
        with patch("app.api.v1.endpoints.ai.get_ai_service") as mock_ai_service:
            mock_ai_service.side_effect = Exception("AI服务连接失败")
            
            response = await async_client.post(
                "/api/v1/ai/chat",
                headers=headers,
                json=chat_request
            )
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "AI服务暂时不可用" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_ai_capabilities_success(async_client, user_token):
    """测试获取AI能力信息成功"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    with patch("app.api.v1.endpoints.ai.get_ai_service") as mock_ai_service:
        mock_service = Mock()
        mock_service.get_available_providers.return_value = ["openai", "dify"]
        mock_service.get_default_provider.return_value = "openai"
        mock_ai_service.return_value = mock_service
        
        response = await async_client.get(
            "/api/v1/ai/capabilities",
            headers=headers
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "available_providers" in data
    assert "default_provider" in data
    assert "features" in data
    assert data["default_provider"] == "openai"
    assert len(data["available_providers"]) == 2
    assert isinstance(data["features"], list)

@pytest.mark.asyncio
async def test_get_ai_capabilities_unauthorized(async_client):
    """测试未登录用户获取AI能力信息"""
    response = await async_client.get("/api/v1/ai/capabilities")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_get_ai_capabilities_service_error(async_client, user_token):
    """测试获取AI能力信息时服务异常"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    with patch("app.api.v1.endpoints.ai.get_ai_service") as mock_ai_service:
        mock_ai_service.side_effect = Exception("配置服务不可用")
        
        response = await async_client.get(
            "/api/v1/ai/capabilities",
            headers=headers
        )
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "无法获取AI能力信息" in response.json()["detail"]

@pytest.mark.asyncio
async def test_check_ai_health_success(async_client, user_token):
    """测试AI健康检查成功"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    with patch("app.api.v1.endpoints.ai.get_ai_service") as mock_ai_service:
        mock_service = Mock()
        mock_service.check_providers_health = AsyncMock(return_value={
            "openai": True,
            "dify": True
        })
        mock_ai_service.return_value = mock_service
        
        response = await async_client.get(
            "/api/v1/ai/health",
            headers=headers
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "providers" in data
    assert "last_check" in data
    assert "message" in data
    assert data["status"] == "healthy"
    assert data["providers"]["openai"] is True
    assert data["providers"]["dify"] is True

@pytest.mark.asyncio
async def test_check_ai_health_degraded(async_client, user_token):
    """测试AI健康检查部分服务不可用"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    with patch("app.api.v1.endpoints.ai.get_ai_service") as mock_ai_service:
        mock_service = Mock()
        mock_service.check_providers_health = AsyncMock(return_value={
            "openai": True,
            "dify": False
        })
        mock_ai_service.return_value = mock_service
        
        response = await async_client.get(
            "/api/v1/ai/health",
            headers=headers
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "degraded"
    assert "部分AI服务不可用" in data["message"]

@pytest.mark.asyncio
async def test_check_ai_health_unhealthy(async_client, user_token):
    """测试AI健康检查所有服务不可用"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    with patch("app.api.v1.endpoints.ai.get_ai_service") as mock_ai_service:
        mock_service = Mock()
        mock_service.check_providers_health = AsyncMock(return_value={
            "openai": False,
            "dify": False
        })
        mock_ai_service.return_value = mock_service
        
        response = await async_client.get(
            "/api/v1/ai/health",
            headers=headers
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "unhealthy"
    assert "AI服务暂时不可用" in data["message"]

@pytest.mark.asyncio
async def test_check_ai_health_service_exception(async_client, user_token):
    """测试AI健康检查服务异常"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    with patch("app.api.v1.endpoints.ai.get_ai_service") as mock_ai_service:
        mock_ai_service.side_effect = Exception("健康检查失败")
        
        response = await async_client.get(
            "/api/v1/ai/health",
            headers=headers
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "unhealthy"
    assert "健康检查失败" in data["message"]

@pytest.mark.asyncio
async def test_get_available_models_success(async_client, user_token):
    """测试获取可用AI模型列表成功"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    with patch("app.api.v1.endpoints.ai.get_ai_service") as mock_ai_service:
        mock_service = Mock()
        mock_service.get_available_models.return_value = ["gpt-3.5-turbo", "gpt-4", "dify-medical"]
        mock_ai_service.return_value = mock_service
        
        response = await async_client.get(
            "/api/v1/ai/models",
            headers=headers
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 3
    assert "gpt-3.5-turbo" in data
    assert "gpt-4" in data
    assert "dify-medical" in data

@pytest.mark.asyncio
async def test_get_available_models_unauthorized(async_client):
    """测试未登录用户获取AI模型列表"""
    response = await async_client.get("/api/v1/ai/models")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_get_available_models_service_error(async_client, user_token):
    """测试获取AI模型列表时服务异常"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    with patch("app.api.v1.endpoints.ai.get_ai_service") as mock_ai_service:
        mock_ai_service.side_effect = Exception("模型服务连接失败")
        
        response = await async_client.get(
            "/api/v1/ai/models",
            headers=headers
        )
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "无法获取可用模型列表" in response.json()["detail"]

@pytest.mark.asyncio
async def test_ai_chat_with_history_context(async_client, user_token, test_conversation):
    """测试AI聊天包含历史上下文"""
    headers = {"Authorization": f"Bearer {user_token}"}
    chat_request = {
        "conversation_id": test_conversation,
        "content": "我刚才问的问题还有其他建议吗？",
        "type": "text"
    }
    
    # Mock chat history with proper objects
    mock_history = [
        Mock(content="我想了解医美项目", sender_type="customer", timestamp=datetime.now()),
        Mock(content="我推荐您考虑肌肤护理类项目", sender_type="ai", timestamp=datetime.now())
    ]
    
    with patch("app.api.v1.endpoints.ai.get_ai_service") as mock_ai_service:
        mock_service = Mock()
        mock_service.get_response = AsyncMock(return_value={
            "content": "除了肌肤护理，您还可以考虑面部轮廓塑形等项目...",
            "timestamp": datetime.now().isoformat()
        })
        mock_ai_service.return_value = mock_service
        
        with patch("app.api.v1.endpoints.ai.ChatService") as mock_chat_service:
            mock_chat = Mock()
            mock_chat.get_conversation_by_id.return_value = Mock(id=test_conversation)
            mock_chat.send_message = AsyncMock()
            mock_chat.send_message.side_effect = [
                Mock(id="msg_user_002", content=chat_request["content"], timestamp=datetime.now()),
                Mock(id="msg_ai_002", content="除了肌肤护理，您还可以考虑面部轮廓塑形等项目...", 
                     timestamp=datetime.now(), type="text")
            ]
            mock_chat.get_conversation_messages.return_value = mock_history
            mock_chat_service.return_value = mock_chat
            
            response = await async_client.post(
                "/api/v1/ai/chat",
                headers=headers,
                json=chat_request
            )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "除了肌肤护理" in data["content"]
    
    # 验证AI服务被调用时包含了历史上下文
    mock_ai_service.return_value.get_response.assert_called_once()
    call_args = mock_ai_service.return_value.get_response.call_args
    assert call_args[0][0] == chat_request["content"]  # 用户消息
    # 验证历史记录已转换为正确格式
    history_arg = call_args[0][1]
    assert len(history_arg) == 2
    assert history_arg[0]["content"] == "我想了解医美项目"
    assert history_arg[0]["sender_type"] == "customer"
    assert history_arg[1]["content"] == "我推荐您考虑肌肤护理类项目"
    assert history_arg[1]["sender_type"] == "ai"

@pytest.mark.asyncio
async def test_ai_chat_different_message_types(async_client, user_token, test_conversation):
    """测试AI聊天支持不同消息类型"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    # 测试语音消息类型
    voice_request = {
        "conversation_id": test_conversation,
        "content": "语音转文字内容：我想了解医美项目",
        "type": "voice"
    }
    
    with patch("app.api.v1.endpoints.ai.get_ai_service") as mock_ai_service:
        mock_service = Mock()
        mock_service.get_response = AsyncMock(return_value={
            "content": "我已收到您的语音消息，关于医美项目...",
            "timestamp": datetime.now().isoformat()
        })
        mock_ai_service.return_value = mock_service
        
        with patch("app.api.v1.endpoints.ai.ChatService") as mock_chat_service:
            mock_chat = Mock()
            mock_chat.get_conversation_by_id.return_value = Mock(id=test_conversation)
            mock_chat.send_message = AsyncMock()
            mock_chat.send_message.side_effect = [
                Mock(id="msg_user_003", content=voice_request["content"], timestamp=datetime.now()),
                Mock(id="msg_ai_003", content="我已收到您的语音消息...", timestamp=datetime.now(), type="text")
            ]
            mock_chat.get_conversation_messages.return_value = []
            mock_chat_service.return_value = mock_chat
            
            response = await async_client.post(
                "/api/v1/ai/chat",
                headers=headers,
                json=voice_request
            )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "语音消息" in data["content"]

@pytest.mark.asyncio
async def test_ai_capabilities_provider_details(async_client, user_token):
    """测试AI能力信息包含提供商详细信息"""
    headers = {"Authorization": f"Bearer {user_token}"}
    
    with patch("app.api.v1.endpoints.ai.get_ai_service") as mock_ai_service:
        mock_service = Mock()
        mock_service.get_available_providers.return_value = ["openai", "dify"]
        mock_service.get_default_provider.return_value = "openai"
        mock_ai_service.return_value = mock_service
        
        response = await async_client.get(
            "/api/v1/ai/capabilities",
            headers=headers
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # 验证提供商信息结构
    providers = data["available_providers"]
    assert len(providers) == 2
    
    openai_provider = next((p for p in providers if p["name"] == "openai"), None)
    assert openai_provider is not None
    assert openai_provider["display_name"] == "OpenAI GPT"
    assert openai_provider["is_available"] is True
    assert "文本生成" in openai_provider["capabilities"]
    
    dify_provider = next((p for p in providers if p["name"] == "dify"), None)
    assert dify_provider is not None
    assert dify_provider["display_name"] == "Dify AI"
    assert "专业对话" in dify_provider["capabilities"]
    
    # 验证功能列表
    features = data["features"]
    assert "文本对话" in features
    assert "多轮对话" in features
    assert "医美专业咨询" in features 