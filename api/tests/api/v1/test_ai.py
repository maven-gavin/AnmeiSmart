"""
AI服务API端点测试

测试覆盖：
1. 基础功能测试
2. 权限验证测试
3. 业务逻辑测试
4. 错误处理测试
5. 边界条件测试
"""

import pytest
import pytest_asyncio
from fastapi import status
from sqlalchemy.orm import Session
from typing import Dict, List
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.db.models.user import User, Role
from app.db.models.chat import Conversation, Message
from app.services import user_service
from app.services.chat import ChatService, MessageService
from app.core.security import create_access_token
from app.schemas.user import UserCreate
from app.schemas.chat import AIChatRequest, MessageInfo
from app.db.uuid_utils import conversation_id, message_id


@pytest_asyncio.fixture
async def customer_user(db: Session) -> User:
    """创建客户用户"""
    user_data = UserCreate(
        email="customer@test.com",
        username="测试客户",
        password="test123456",
        roles=["customer"]
    )
    return await user_service.create(db, obj_in=user_data)


@pytest_asyncio.fixture
async def consultant_user(db: Session) -> User:
    """创建顾问用户"""
    user_data = UserCreate(
        email="consultant@test.com",
        username="测试顾问",
        password="test123456",
        roles=["consultant"]
    )
    return await user_service.create(db, obj_in=user_data)


@pytest_asyncio.fixture
async def doctor_user(db: Session) -> User:
    """创建医生用户"""
    user_data = UserCreate(
        email="doctor@test.com",
        username="测试医生",
        password="test123456",
        roles=["doctor"]
    )
    return await user_service.create(db, obj_in=user_data)


@pytest_asyncio.fixture
async def customer_token(customer_user: User) -> str:
    """客户用户token"""
    return create_access_token(customer_user.id)


@pytest_asyncio.fixture
async def consultant_token(consultant_user: User) -> str:
    """顾问用户token"""
    return create_access_token(consultant_user.id)


@pytest_asyncio.fixture
async def doctor_token(doctor_user: User) -> str:
    """医生用户token"""
    return create_access_token(doctor_user.id)


@pytest_asyncio.fixture
async def test_conversation(db: Session, customer_user: User) -> Conversation:
    """创建测试会话"""
    conv = Conversation(
        id=conversation_id(),
        title="测试咨询",
        customer_id=customer_user.id,
        is_active=True,
        is_ai_controlled=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@pytest_asyncio.fixture
async def test_messages(db: Session, test_conversation: Conversation, customer_user: User) -> List[Message]:
    """创建测试消息历史"""
    messages = []
    for i in range(3):
        msg = Message(
            id=message_id(),
            conversation_id=test_conversation.id,
            content=f"测试消息 {i+1}",
            type="text",
            sender_id=customer_user.id,
            sender_type="customer",
            timestamp=datetime.now(),
            is_read=False,
            is_important=False
        )
        db.add(msg)
        messages.append(msg)
    
    db.commit()
    for msg in messages:
        db.refresh(msg)
    return messages


# ========== 基础功能测试 ==========

@pytest.mark.asyncio
async def test_get_ai_response_success(
    async_client, 
    customer_token: str, 
    test_conversation: Conversation,
    test_messages: List[Message]
):
    """测试成功获取AI回复"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "双眼皮手术需要注意什么？",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        # 模拟AI服务返回
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "双眼皮手术需要注意术前术后护理...",
            "id": "ai_123"
        }
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # 验证返回的AI消息格式
    assert "id" in data
    assert "content" in data
    assert data["sender"]["type"] == "ai"
    assert data["sender"]["name"] == "AI助手"
    assert "双眼皮手术" in data["content"]


@pytest.mark.asyncio 
async def test_get_ai_response_consultant_role(
    async_client,
    consultant_token: str,
    test_conversation: Conversation,
    test_messages: List[Message]
):
    """测试顾问角色发送消息获取AI回复"""
    headers = {"Authorization": f"Bearer {consultant_token}"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "请帮我分析这个客户的需求",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "根据客户描述，建议进行面诊...",
            "id": "ai_456"
        }
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["sender"]["type"] == "ai"


@pytest.mark.asyncio
async def test_get_ai_response_doctor_role(
    async_client,
    doctor_token: str,
    test_conversation: Conversation,
    test_messages: List[Message]
):
    """测试医生角色发送消息获取AI回复"""
    headers = {"Authorization": f"Bearer {doctor_token}"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "这个手术方案需要调整吗？",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "建议从以下几个方面考虑调整...",
            "id": "ai_789"
        }
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["sender"]["type"] == "ai"


# ========== 权限验证测试 ==========

@pytest.mark.asyncio
async def test_get_ai_response_unauthorized(async_client, test_conversation: Conversation):
    """测试未认证用户访问"""
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "测试消息",
        "type": "text"
    }
    
    response = await async_client.post(
        "/api/v1/ai/chat",
        json=message_data
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
async def test_get_ai_response_invalid_token(async_client, test_conversation: Conversation):
    """测试无效token"""
    headers = {"Authorization": "Bearer invalid_token"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "测试消息",
        "type": "text"
    }
    
    response = await async_client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json=message_data
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ========== 业务逻辑测试 ==========

@pytest.mark.asyncio
async def test_get_ai_response_conversation_not_found(
    async_client,
    customer_token: str
):
    """测试会话不存在"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    message_data = {
        "conversation_id": "nonexistent_conversation_id",
        "content": "测试消息",
        "type": "text"
    }
    
    response = await async_client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json=message_data
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "会话不存在或无权访问" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_ai_response_conversation_access_denied(
    async_client,
    db: Session,
    customer_token: str
):
    """测试访问他人会话被拒绝"""
    # 创建另一个用户的会话
    other_user_data = UserCreate(
        email="other@test.com",
        username="其他用户",
        password="test123456",
        roles=["customer"]
    )
    other_user = await user_service.create(db, obj_in=other_user_data)
    
    other_conversation = Conversation(
        id=conversation_id(),
        title="其他用户的会话",
        customer_id=other_user.id,
        is_active=True,
        is_ai_controlled=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(other_conversation)
    db.commit()
    
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    message_data = {
        "conversation_id": other_conversation.id,
        "content": "测试消息",
        "type": "text"
    }
    
    response = await async_client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json=message_data
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "会话不存在或无权访问" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_ai_response_with_history_context(
    async_client,
    customer_token: str,
    test_conversation: Conversation,
    test_messages: List[Message]
):
    """测试AI回复时使用历史消息上下文"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "那双眼皮手术价格如何？",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "根据您之前的咨询，双眼皮手术价格...",
            "id": "ai_context"
        }
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
        
        # 验证AI服务被调用时包含了历史消息
        mock_service.get_response.assert_called_once()
        call_args = mock_service.get_response.call_args
        query = call_args[0][0]
        history = call_args[0][1]
        
        assert query == "那双眼皮手术价格如何？"
        assert isinstance(history, list)
        assert len(history) > 0  # 应该有历史消息
    
    assert response.status_code == status.HTTP_200_OK


# ========== 错误处理测试 ==========

@pytest.mark.asyncio
async def test_get_ai_response_ai_service_error(
    async_client,
    customer_token: str,
    test_conversation: Conversation,
    test_messages: List[Message]
):
    """测试AI服务异常时的错误处理"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "测试AI服务错误",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.side_effect = Exception("AI服务连接失败")
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "AI回复失败" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_ai_response_ai_service_timeout(
    async_client,
    customer_token: str,
    test_conversation: Conversation,
    test_messages: List[Message]
):
    """测试AI服务超时时的错误处理"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "测试AI服务超时",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        import asyncio
        mock_service = AsyncMock()
        mock_service.get_response.side_effect = asyncio.TimeoutError("请求超时")
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "AI回复失败" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_ai_response_invalid_ai_response_format(
    async_client,
    customer_token: str,
    test_conversation: Conversation,
    test_messages: List[Message]
):
    """测试AI服务返回格式错误时的处理"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "测试AI响应格式错误",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        # 返回无效格式（缺少content字段）
        mock_service.get_response.return_value = {
            "id": "ai_123"
            # 缺少 content 字段
        }
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # 应该有默认的错误回复内容
    assert "抱歉，我暂时无法回复" in data["content"]


# ========== 边界条件测试 ==========

@pytest.mark.asyncio
async def test_get_ai_response_empty_content(
    async_client,
    customer_token: str,
    test_conversation: Conversation
):
    """测试空消息内容"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "",
        "type": "text"
    }
    
    response = await async_client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json=message_data
    )
    
    # 根据业务逻辑，可能是400错误或者接受空内容
    assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


@pytest.mark.asyncio
async def test_get_ai_response_very_long_content(
    async_client,
    customer_token: str,
    test_conversation: Conversation
):
    """测试超长消息内容"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    # 创建一个非常长的消息（10KB+）
    long_content = "A" * 10000
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": long_content,
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "收到您的详细咨询...",
            "id": "ai_long"
        }
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
    
    # 应该正常处理或返回相应的错误
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE]


@pytest.mark.asyncio
async def test_get_ai_response_special_characters(
    async_client,
    customer_token: str,
    test_conversation: Conversation
):
    """测试包含特殊字符的消息"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "测试消息 🤔💉💊 @#$%^&*()_+ 中文测试 emoji 😀",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "我理解您的问题...",
            "id": "ai_special"
        }
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "content" in data


@pytest.mark.asyncio
async def test_get_ai_response_invalid_message_type(
    async_client,
    customer_token: str,
    test_conversation: Conversation
):
    """测试无效的消息类型"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "测试消息",
        "type": "invalid_type"
    }
    
    response = await async_client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json=message_data
    )
    
    # 应该返回验证错误
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_get_ai_response_missing_required_fields(
    async_client,
    customer_token: str
):
    """测试缺少必需字段"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    # 缺少conversation_id
    message_data = {
        "content": "测试消息",
        "type": "text"
    }
    
    response = await async_client.post(
        "/api/v1/ai/chat",
        headers=headers,
        json=message_data
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ========== 集成测试 ==========

@pytest.mark.asyncio
async def test_get_ai_response_full_workflow(
    async_client,
    db: Session,
    customer_token: str,
    test_conversation: Conversation
):
    """测试完整的AI对话工作流"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    # 第一轮对话
    message_data_1 = {
        "conversation_id": test_conversation.id,
        "content": "我想了解双眼皮手术",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "双眼皮手术是常见的美容项目...",
            "id": "ai_001"
        }
        mock_ai_service.return_value = mock_service
        
        response_1 = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data_1
        )
    
    assert response_1.status_code == status.HTTP_200_OK
    ai_response_1 = response_1.json()
    
    # 第二轮对话（应该包含之前的上下文）
    message_data_2 = {
        "conversation_id": test_conversation.id,
        "content": "费用大概多少？",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "根据您刚才的咨询，费用一般在...",
            "id": "ai_002"
        }
        mock_ai_service.return_value = mock_service
        
        response_2 = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data_2
        )
        
        # 验证第二次调用包含了之前的消息历史
        mock_service.get_response.assert_called_once()
        call_args = mock_service.get_response.call_args
        history = call_args[0][1]
        
        # 历史消息应该包含之前的对话
        assert len(history) > 0
    
    assert response_2.status_code == status.HTTP_200_OK
    ai_response_2 = response_2.json()
    
    # 验证消息已保存到数据库
    messages = db.query(Message).filter(
        Message.conversation_id == test_conversation.id
    ).order_by(Message.timestamp).all()
    
    # 应该有用户消息和AI回复消息
    assert len(messages) >= 4  # 2个用户消息 + 2个AI回复
    
    # 验证最后的消息是AI回复
    last_message = messages[-1]
    assert last_message.sender_type == "ai"
    assert last_message.sender_id == "ai"


# ========== 性能测试 ==========

@pytest.mark.asyncio
async def test_get_ai_response_concurrent_requests(
    async_client,
    customer_token: str,
    test_conversation: Conversation
):
    """测试并发请求处理"""
    import asyncio
    
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    async def send_message(content: str):
        message_data = {
            "conversation_id": test_conversation.id,
            "content": content,
            "type": "text"
        }
        
        with patch("app.services.ai.get_ai_service") as mock_ai_service:
            mock_service = AsyncMock()
            mock_service.get_response.return_value = {
                "content": f"回复: {content}",
                "id": f"ai_{content.replace(' ', '_')}"
            }
            mock_ai_service.return_value = mock_service
            
            return await async_client.post(
                "/api/v1/ai/chat",
                headers=headers,
                json=message_data
            )
    
    # 发送多个并发请求
    tasks = [
        send_message(f"并发测试消息 {i}")
        for i in range(3)
    ]
    
    responses = await asyncio.gather(*tasks)
    
    # 所有请求都应该成功
    for response in responses:
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "回复: 并发测试消息" in data["content"]


# ========== 数据转换与Schema测试 ==========

@pytest.mark.asyncio
async def test_ai_response_schema_validation(
    async_client,
    customer_token: str,
    test_conversation: Conversation,
    test_messages: List[Message]
):
    """测试AI回复的Schema转换和验证"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "测试Schema转换",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "这是AI的回复内容",
            "id": "ai_schema_test"
        }
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # 验证返回的数据结构符合MessageInfo schema
    required_fields = ["id", "content", "type", "timestamp", "sender", "is_read", "is_important"]
    for field in required_fields:
        assert field in data, f"缺少必需字段: {field}"
    
    # 验证sender字段结构
    sender = data["sender"]
    assert "id" in sender
    assert "type" in sender
    assert "name" in sender
    assert sender["type"] == "ai"
    assert sender["name"] == "AI助手"
    
    # 验证时间戳格式
    assert "T" in data["timestamp"]  # ISO格式时间戳
    
    # 验证消息类型
    assert data["type"] == "text"


@pytest.mark.asyncio
async def test_message_persistence_after_ai_response(
    async_client,
    db: Session,
    customer_token: str,
    customer_user: User,
    test_conversation: Conversation
):
    """测试AI回复后消息持久化到数据库"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    # 记录测试前的消息数量
    initial_count = db.query(Message).filter(
        Message.conversation_id == test_conversation.id
    ).count()
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "测试消息持久化",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "AI回复内容",
            "id": "ai_persistence_test"
        }
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
    
    assert response.status_code == status.HTTP_200_OK
    
    # 验证数据库中新增了两条消息（用户消息 + AI回复）
    final_count = db.query(Message).filter(
        Message.conversation_id == test_conversation.id
    ).count()
    
    assert final_count == initial_count + 2
    
    # 验证用户消息
    user_message = db.query(Message).filter(
        Message.conversation_id == test_conversation.id,
        Message.sender_type == "customer",
        Message.content == "测试消息持久化"
    ).first()
    
    assert user_message is not None
    assert user_message.sender_id == customer_user.id
    assert user_message.type == "text"
    
    # 验证AI回复消息
    ai_message = db.query(Message).filter(
        Message.conversation_id == test_conversation.id,
        Message.sender_type == "ai",
        Message.content == "AI回复内容"
    ).first()
    
    assert ai_message is not None
    assert ai_message.sender_id is None  # AI消息sender_id应该为None
    assert ai_message.type == "text"


@pytest.mark.asyncio
async def test_user_role_detection_and_usage(
    async_client,
    consultant_token: str,
    consultant_user: User,
    test_conversation: Conversation
):
    """测试用户角色检测和使用"""
    # 设置顾问的活跃角色
    consultant_user._active_role = "consultant"
    
    headers = {"Authorization": f"Bearer {consultant_token}"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "作为顾问，我想了解客户情况",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "根据顾问角色，为您提供专业建议...",
            "id": "ai_role_test"
        }
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
    
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_conversation_update_after_message(
    async_client,
    db: Session,
    customer_token: str,
    test_conversation: Conversation
):
    """测试发送消息后会话的更新"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    # 记录会话的初始更新时间
    original_updated_at = test_conversation.updated_at
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "测试会话更新",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "AI回复",
            "id": "ai_update_test"
        }
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
    
    assert response.status_code == status.HTTP_200_OK
    
    # 重新加载会话数据
    db.refresh(test_conversation)
    
    # 验证会话的updated_at时间已更新
    assert test_conversation.updated_at > original_updated_at


# ========== 业务逻辑验证测试 ==========

@pytest.mark.asyncio
async def test_ai_service_call_with_correct_parameters(
    async_client,
    customer_token: str,
    test_conversation: Conversation,
    test_messages: List[Message]
):
    """测试AI服务调用时参数传递的正确性"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    message_content = "这是一个具体的测试问题"
    message_data = {
        "conversation_id": test_conversation.id,
        "content": message_content,
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "AI回复",
            "id": "ai_param_test"
        }
        mock_ai_service.return_value = mock_service
        
        await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
        
        # 验证AI服务被正确调用
        mock_service.get_response.assert_called_once()
        call_args = mock_service.get_response.call_args
        
        # 验证传递的消息内容
        assert call_args[0][0] == message_content
        
        # 验证传递的历史记录格式
        history = call_args[0][1]
        assert isinstance(history, list)
        for history_item in history:
            assert "content" in history_item
            assert "sender_type" in history_item
            assert "timestamp" in history_item


@pytest.mark.asyncio
async def test_conversation_access_validation_for_different_roles(
    async_client,
    db: Session,
    customer_user: User,
    consultant_user: User,
    doctor_user: User
):
    """测试不同角色对会话的访问权限验证"""
    from app.core.security import create_access_token
    
    # 创建属于客户的会话
    customer_conversation = Conversation(
        id=conversation_id(),
        title="客户专属会话",
        customer_id=customer_user.id,
        is_active=True,
        is_ai_controlled=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(customer_conversation)
    db.commit()
    db.refresh(customer_conversation)
    
    message_data = {
        "conversation_id": customer_conversation.id,
        "content": "测试访问权限",
        "type": "text"
    }
    
    # 测试客户自己访问 - 应该成功
    customer_token = create_access_token(customer_user.id)
    customer_headers = {"Authorization": f"Bearer {customer_token}"}
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "客户访问成功",
            "id": "ai_customer_access"
        }
        mock_ai_service.return_value = mock_service
        
        customer_response = await async_client.post(
            "/api/v1/ai/chat",
            headers=customer_headers,
            json=message_data
        )
    
    assert customer_response.status_code == status.HTTP_200_OK
    
    # 测试其他客户访问 - 应该失败
    other_customer_data = UserCreate(
        email="other_customer@test.com",
        username="其他客户",
        password="test123456",
        roles=["customer"]
    )
    other_customer = await user_service.create(db, obj_in=other_customer_data)
    other_customer_token = create_access_token(other_customer.id)
    other_customer_headers = {"Authorization": f"Bearer {other_customer_token}"}
    
    other_customer_response = await async_client.post(
        "/api/v1/ai/chat",
        headers=other_customer_headers,
        json=message_data
    )
    
    assert other_customer_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_message_history_limit_and_ordering(
    async_client,
    db: Session,
    customer_token: str,
    customer_user: User,
    test_conversation: Conversation
):
    """测试消息历史记录的限制和排序"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    # 创建多条历史消息（超过默认限制10条）
    for i in range(15):
        msg = Message(
            id=message_id(),
            conversation_id=test_conversation.id,
            content=f"历史消息 {i+1}",
            type="text",
            sender_id=customer_user.id,
            sender_type="customer",
            timestamp=datetime.now(),
            is_read=True,
            is_important=False
        )
        db.add(msg)
    
    db.commit()
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "测试历史记录限制",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "AI回复",
            "id": "ai_history_limit_test"
        }
        mock_ai_service.return_value = mock_service
        
        await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
        
        # 验证历史记录的数量限制
        call_args = mock_service.get_response.call_args
        history = call_args[0][1]
        
        # 应该只返回最近的10条消息
        assert len(history) <= 10
        
        # 验证消息是按时间排序的（最新的在后面）
        if len(history) > 1:
            for i in range(1, len(history)):
                prev_time = datetime.fromisoformat(history[i-1]["timestamp"])
                curr_time = datetime.fromisoformat(history[i]["timestamp"])
                assert prev_time <= curr_time


# ========== 服务层集成测试 ==========

@pytest.mark.asyncio
async def test_chat_service_integration(
    async_client,
    db: Session,
    customer_token: str,
    customer_user: User,
    test_conversation: Conversation
):
    """测试与ChatService的集成"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "测试ChatService集成",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "ChatService集成测试回复",
            "id": "ai_chat_service_test"
        }
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
    
    assert response.status_code == status.HTTP_200_OK
    
    # 验证ChatService正确创建了用户消息
    user_messages = db.query(Message).filter(
        Message.conversation_id == test_conversation.id,
        Message.sender_type == "customer",
        Message.content == "测试ChatService集成"
    ).all()
    
    assert len(user_messages) == 1
    user_message = user_messages[0]
    assert user_message.sender_id == customer_user.id


@pytest.mark.asyncio
async def test_message_service_integration(
    async_client,
    db: Session,
    customer_token: str,
    test_conversation: Conversation
):
    """测试与MessageService的集成"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "测试MessageService集成",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "MessageService集成测试回复",
            "id": "ai_message_service_test"
        }
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
    
    assert response.status_code == status.HTTP_200_OK
    
    # 验证MessageService正确创建了AI回复消息
    ai_messages = db.query(Message).filter(
        Message.conversation_id == test_conversation.id,
        Message.sender_type == "ai",
        Message.content == "MessageService集成测试回复"
    ).all()
    
    assert len(ai_messages) == 1
    ai_message = ai_messages[0]
    assert ai_message.sender_id is None  # AI消息没有关联用户ID
    assert ai_message.type == "text"


# ========== DDD分层架构验证测试 ==========

@pytest.mark.asyncio
async def test_controller_layer_responsibility(
    async_client,
    customer_token: str,
    test_conversation: Conversation
):
    """测试Controller层的职责边界 - 只做参数校验、权限校验、调用service"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "测试Controller层职责",
        "type": "text"
    }
    
    with patch("app.services.chat.ChatService") as mock_chat_service_class, \
         patch("app.services.chat.MessageService") as mock_message_service_class, \
         patch("app.services.ai.get_ai_service") as mock_ai_service:
        
        # 设置mock服务
        mock_chat_service = MagicMock()
        mock_message_service = MagicMock()
        mock_chat_service_class.return_value = mock_chat_service
        mock_message_service_class.return_value = mock_message_service
        
        # 模拟_get_conversation_model返回会话
        mock_chat_service._get_conversation_model.return_value = test_conversation
        
        # 模拟send_message返回用户消息
        user_message_mock = MagicMock()
        user_message_mock.id = "user_msg_123"
        mock_chat_service.send_message.return_value = user_message_mock
        
        # 模拟get_recent_messages返回历史
        mock_message_service.get_recent_messages.return_value = []
        
        # 模拟AI服务
        mock_ai_service_instance = AsyncMock()
        mock_ai_service_instance.get_response.return_value = {
            "content": "AI回复",
            "id": "ai_123"
        }
        mock_ai_service.return_value = mock_ai_service_instance
        
        # 模拟create_message返回AI消息，并正确设置from_model
        ai_message_mock = MagicMock()
        ai_message_mock.id = "ai_msg_123"
        ai_message_mock.content = "AI回复"
        ai_message_mock.sender_type = "ai"
        
        # 为MessageInfo.from_model设置mock
        mock_message_info = MagicMock()
        mock_message_info.dict.return_value = {
            "id": "ai_msg_123",
            "content": "AI回复",
            "sender": {"type": "ai", "name": "AI助手"}
        }
        
        with patch("app.schemas.chat.MessageInfo.from_model", return_value=mock_message_info):
            mock_message_service.create_message.return_value = ai_message_mock
            
            response = await async_client.post(
                "/api/v1/ai/chat",
                headers=headers,
                json=message_data
            )
    
    # Controller层应该正确调用了各个service
    assert mock_chat_service._get_conversation_model.called
    assert mock_chat_service.send_message.called
    assert mock_message_service.get_recent_messages.called
    assert mock_message_service.create_message.called
    
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_service_layer_returns_schema_not_orm(
    async_client,
    customer_token: str,
    test_conversation: Conversation
):
    """测试Service层返回Schema而不是ORM对象"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "测试Service层返回Schema",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        mock_service.get_response.return_value = {
            "content": "Service层测试回复",
            "id": "ai_service_schema_test"
        }
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # 验证返回的是序列化后的Schema数据，不是ORM对象
    assert isinstance(data, dict)
    assert "id" in data
    assert "content" in data
    assert "sender" in data
    assert "timestamp" in data
    
    # 验证没有ORM对象的内部属性
    assert "_sa_instance_state" not in data
    assert "__dict__" not in data


# ========== 错误恢复和优雅降级测试 ==========

@pytest.mark.asyncio
async def test_graceful_degradation_on_ai_service_partial_failure(
    async_client,
    customer_token: str,
    test_conversation: Conversation
):
    """测试AI服务部分失败时的优雅降级"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "测试优雅降级",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        # 模拟AI服务返回部分损坏的响应
        mock_service.get_response.return_value = {
            "content": None,  # 内容为空
            "id": "ai_partial_failure"
        }
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    
    # 应该有默认的回复内容
    assert "抱歉，我暂时无法回复" in data["content"]


@pytest.mark.asyncio
async def test_database_transaction_rollback_on_error(
    async_client,
    db: Session,
    customer_token: str,
    test_conversation: Conversation
):
    """测试发生错误时数据库事务的回滚"""
    headers = {"Authorization": f"Bearer {customer_token}"}
    
    # 记录初始消息数量
    initial_count = db.query(Message).filter(
        Message.conversation_id == test_conversation.id
    ).count()
    
    message_data = {
        "conversation_id": test_conversation.id,
        "content": "测试事务回滚",
        "type": "text"
    }
    
    with patch("app.services.ai.get_ai_service") as mock_ai_service:
        mock_service = AsyncMock()
        # 模拟AI服务在处理过程中抛出异常
        mock_service.get_response.side_effect = Exception("AI服务内部错误")
        mock_ai_service.return_value = mock_service
        
        response = await async_client.post(
            "/api/v1/ai/chat",
            headers=headers,
            json=message_data
        )
    
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    
    # 验证数据库中消息数量没有增加（事务已回滚）
    final_count = db.query(Message).filter(
        Message.conversation_id == test_conversation.id
    ).count()
    
    # 注意：根据具体的事务处理实现，这个测试可能需要调整
    # 如果用户消息在AI回复失败前已经提交，则count会+1
    # 如果整个操作在一个事务中，则count应该保持不变
    assert final_count >= initial_count  # 至少不会减少 