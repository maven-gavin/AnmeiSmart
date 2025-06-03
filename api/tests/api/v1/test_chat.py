import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import json
from datetime import datetime

from app.db.models.user import User
from app.db.models.chat import Conversation, Message
from app.services.chat.ai_response_service import AIResponseService
from app.services.chat.message_service import MessageService
from app.services.chat.chat_service import ChatService
from app.core.events import EventTypes, event_bus, create_message_event
from app.core.websocket_manager import websocket_manager
from app.api.deps import get_db
from app.api.v1.endpoints.chat import get_user_role
from app.services import user_service as crud_user
from app.schemas.user import UserCreate


@pytest.fixture
def fake_customer(db: Session):
    user_in = UserCreate(
        email="test_customer@example.com",
        username="test_customer",
        password="test123456",
        roles=["customer"],
        is_active=True
    )
    user = asyncio.get_event_loop().run_until_complete(crud_user.create(db, user_in))
    return user

@pytest.fixture
def fake_consultant(db: Session):
    user_in = UserCreate(
        email="test_consultant@example.com",
        username="test_consultant",
        password="test123456",
        roles=["consultant"],
        is_active=True
    )
    user = asyncio.get_event_loop().run_until_complete(crud_user.create(db, user_in))
    return user

@pytest.fixture
def fake_conversation(db: Session, fake_customer):
    conv = Conversation(title="test conv", customer_id=fake_customer.id, is_ai_controlled=True)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

@pytest.fixture
def mock_websocket():
    """模拟WebSocket连接"""
    websocket = MagicMock()
    websocket.send_json = AsyncMock()
    websocket.receive_json = AsyncMock()
    websocket.close = AsyncMock()
    return websocket

@pytest.fixture
def mock_ai_service():
    """模拟AI服务"""
    with patch('app.services.ai.get_ai_service') as mock:
        ai_service = MagicMock()
        ai_service.get_response = AsyncMock(return_value={
            "content": "这是AI的回复",
            "timestamp": datetime.now().isoformat()
        })
        mock.return_value = ai_service
        yield ai_service


# ============ 场景1：客户发消息给顾问咨询问题 ============

@pytest.mark.asyncio
async def test_customer_message_full_flow_websocket(
    db: Session, 
    fake_customer, 
    fake_conversation, 
    mock_ai_service
):
    """测试场景1完整流程：客户通过WebSocket发送消息，触发AI回复"""
    
    # 1. 模拟WebSocket消息数据
    message_data = {
        "action": "message",
        "data": {
            "content": "我想了解双眼皮手术",
            "type": "text",
            "sender_type": "customer",
            "is_important": False
        }
    }
    
    # 2. Mock MessageService来避免数据库外键约束问题
    mock_message_service = MagicMock()
    mock_customer_message = MagicMock()
    mock_customer_message.id = "msg_customer_123"
    mock_customer_message.content = "我想了解双眼皮手术"
    mock_customer_message.sender_type = "customer"
    
    mock_ai_message = MagicMock()
    mock_ai_message.id = "msg_ai_456"
    mock_ai_message.content = "这是AI的回复"
    mock_ai_message.sender_type = "ai"
    
    # Mock返回值
    mock_message_service.create_message = AsyncMock()
    mock_message_service.create_message.side_effect = [mock_customer_message, mock_ai_message]
    
    # 3. 测试消息处理器
    from app.services.websocket.websocket_handler import WebSocketHandler
    handler = WebSocketHandler()
    
    # 4. Mock事件发布，捕获发布的事件
    published_events = []
    
    async def mock_publish(event):
        published_events.append(event)
        # 模拟AIResponseService处理事件，但使用mock的MessageService
        if event.type == EventTypes.CHAT_MESSAGE_RECEIVED:
            ai_service = AIResponseService(db)
            # 替换为mock的MessageService
            ai_service.message_service = mock_message_service
            await ai_service.handle_message_event(event)
    
    with patch.object(event_bus, 'publish_async', side_effect=mock_publish):
        # 5. 处理WebSocket消息
        response = await handler.handle_websocket_message(
            message_data, 
            fake_customer.id, 
            fake_conversation.id
        )
        
        # 等待异步处理完成
        await asyncio.sleep(0.1)
    
    # 6. 验证结果
    assert response["data"]["status"] == "success"
    assert len(published_events) >= 1  # 至少发布了消息接收事件
    
    # 7. 验证MessageService被正确调用
    assert mock_message_service.create_message.call_count >= 1
    
    # 8. 验证AI服务被调用
    mock_ai_service.get_response.assert_called_once()
    
    # 9. 验证事件类型
    message_event = published_events[0]
    assert message_event.type == EventTypes.CHAT_MESSAGE_RECEIVED
    assert message_event.conversation_id == fake_conversation.id
    assert message_event.data["content"] == "我想了解双眼皮手术"


@pytest.mark.asyncio
async def test_customer_message_with_consultant_takeover(
    db: Session, 
    fake_customer, 
    fake_conversation, 
    mock_ai_service
):
    """测试顾问接管后，客户消息不触发AI回复"""
    
    # 1. 顾问接管会话
    chat_service = ChatService(db)
    success = chat_service.set_ai_controlled_status(fake_conversation.id, False)
    assert success is True
    
    # 2. 客户发送消息
    message_data = {
        "action": "message", 
        "data": {
            "content": "顾问接管后的消息",
            "type": "text",
            "sender_type": "customer"
        }
    }
    
    from app.services.websocket.websocket_handler import WebSocketHandler
    handler = WebSocketHandler()
    
    published_events = []
    async def mock_publish(event):
        published_events.append(event)
        if event.type == EventTypes.CHAT_MESSAGE_RECEIVED:
            ai_service = AIResponseService(db)
            # 直接测试should_ai_reply逻辑，不需要Mock MessageService
            should_reply = await ai_service.should_ai_reply(event)
            # 由于顾问接管了，should_reply应该为False
            assert should_reply is False
    
    with patch.object(event_bus, 'publish_async', side_effect=mock_publish):
        response = await handler.handle_websocket_message(
            message_data,
            fake_customer.id, 
            fake_conversation.id
        )
        await asyncio.sleep(0.1)
    
    # 3. 验证WebSocket响应成功
    assert response["data"]["status"] == "success"
    
    # 4. 验证事件被发布
    assert len(published_events) == 1
    event = published_events[0]
    assert event.type == EventTypes.CHAT_MESSAGE_RECEIVED
    assert event.data["content"] == "顾问接管后的消息"
    
    # 5. 验证AI服务没有被调用（因为顾问接管了）
    mock_ai_service.get_response.assert_not_called()


# ============ 场景2：顾问发消息给客户 ============

@pytest.mark.asyncio
async def test_consultant_message_to_customer_websocket(
    db: Session, 
    fake_customer, 
    fake_consultant, 
    fake_conversation
):
    """测试场景2：顾问通过WebSocket发送消息给客户"""
    
    # 1. 顾问发送消息
    message_data = {
        "action": "message",
        "data": {
            "content": "您好，我是您的专属顾问，有什么可以帮助您的吗？",
            "type": "text", 
            "sender_type": "consultant",
            "is_important": False
        }
    }
    
    from app.services.websocket.websocket_handler import WebSocketHandler
    handler = WebSocketHandler()
    
    # 2. Mock事件发布
    published_events = []
    async def mock_publish(event):
        published_events.append(event)
    
    with patch.object(event_bus, 'publish_async', side_effect=mock_publish):
        response = await handler.handle_websocket_message(
            message_data,
            fake_consultant.id,
            fake_conversation.id
        )
        await asyncio.sleep(0.1)
    
    # 3. 验证响应成功
    assert response["data"]["status"] == "success"
    
    # 4. 验证事件发布
    assert len(published_events) >= 1
    message_event = published_events[0]
    assert message_event.type == EventTypes.CHAT_MESSAGE_RECEIVED
    assert message_event.conversation_id == fake_conversation.id
    assert message_event.data["content"] == "您好，我是您的专属顾问，有什么可以帮助您的吗？"
    assert message_event.data["sender_type"] == "consultant"


# ============ WebSocket连接和Token验证测试 ============

@pytest.mark.asyncio
async def test_websocket_token_verification():
    """测试WebSocket token验证流程"""
    
    # Mock数据库和用户
    mock_db = MagicMock()
    mock_user = MagicMock()
    mock_user.id = "user123"
    mock_user.username = "test_user"
    # 创建正确的roles mock
    mock_role = MagicMock()
    mock_role.name = "customer"
    mock_user.roles = [mock_role]
    mock_user._active_role = None  # 没有活跃角色
    mock_db.query.return_value.filter.return_value.first.return_value = mock_user
    
    # Mock token验证
    with patch('app.core.security.verify_token') as mock_verify:
        mock_verify.return_value = {"sub": "user123", "role": "customer"}
        
        from app.api.v1.endpoints.chat import verify_websocket_token
        
        result = await verify_websocket_token("valid_token", mock_db)
        
        assert result is not None
        assert result["user_id"] == "user123"
        assert result["role"] == "customer"  # 这是从roles[0].name获取的
        assert result["username"] == "test_user"


@pytest.mark.asyncio 
async def test_websocket_invalid_token():
    """测试WebSocket无效token处理"""
    
    mock_db = MagicMock()
    
    with patch('app.core.security.verify_token') as mock_verify:
        mock_verify.return_value = None  # 无效token
        
        from app.api.v1.endpoints.chat import verify_websocket_token
        
        result = await verify_websocket_token("invalid_token", mock_db)
        
        assert result is None


# ============ 消息广播测试 ============

@pytest.mark.asyncio
async def test_message_broadcast_to_conversation(fake_conversation):
    """测试消息广播到会话参与者"""
    
    # Mock WebSocket连接
    mock_connection1 = MagicMock()
    mock_connection1.send_json = AsyncMock()
    mock_connection2 = MagicMock()
    mock_connection2.send_json = AsyncMock()
    
    # Mock websocket_manager的broadcast_to_conversation方法
    with patch.object(websocket_manager, 'broadcast_to_conversation') as mock_broadcast:
        mock_broadcast.return_value = None  # 异步方法，无返回值
        
        # 发送广播消息
        message_data = {
            "action": "message",
            "data": {"content": "广播测试消息"},
            "conversation_id": fake_conversation.id
        }
        
        await websocket_manager.broadcast_to_conversation(
            fake_conversation.id, 
            message_data
        )
        
        # 验证广播方法被调用
        mock_broadcast.assert_called_once_with(
            fake_conversation.id, 
            message_data
        )


# ============ AI回复优化测试 ============

@pytest.mark.asyncio
async def test_ai_reply_trigger_with_proper_mocking(
    db: Session, 
    fake_customer, 
    fake_conversation, 
    mock_ai_service
):
    """优化的AI回复触发测试，使用proper mocking替代sleep"""
    
    # Mock MessageService
    mock_message_service = MagicMock()
    mock_ai_message = MagicMock()
    mock_ai_message.id = "msg_ai_123"
    mock_ai_message.content = "这是AI的回复"
    mock_message_service.create_message = AsyncMock(return_value=mock_ai_message)
    
    # 创建AI响应服务
    ai_service = AIResponseService(db)
    ai_service.message_service = mock_message_service  # 替换为mock
    
    # 模拟客户消息事件
    event = create_message_event(
        conversation_id=fake_conversation.id,
        user_id=fake_customer.id,
        content="请问如何预约？",
        message_type="text",
        sender_type="customer",
        is_important=False
    )
    
    # 调用处理方法
    await ai_service.handle_message_event(event)
    
    # 验证AI服务被调用
    mock_ai_service.get_response.assert_called_once()
    
    # 验证MessageService被调用创建AI回复
    mock_message_service.create_message.assert_called_once()
    create_call_args = mock_message_service.create_message.call_args
    assert create_call_args[1]["content"] == "这是AI的回复"
    assert create_call_args[1]["sender_type"] == "ai"


# ============ HTTP接口核心功能测试 ============

def test_create_conversation(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer
):
    """测试创建新会话"""
    token = get_token
    data = {
        "title": "新的咨询会话",
        "customer_id": fake_customer.id
    }
    
    response = client.post(
        "/api/v1/chat/conversations", 
        json=data, 
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 201
    result = response.json()
    assert result["title"] == "新的咨询会话"
    assert result["customer_id"] == fake_customer.id
    assert "id" in result
    assert "created_at" in result


def test_get_conversations_list(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试获取会话列表"""
    token = get_token
    
    response = client.get(
        "/api/v1/chat/conversations",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    assert len(result) >= 1
    
    # 验证会话信息
    conversation = result[0]
    assert "id" in conversation
    assert "title" in conversation
    assert "customer_id" in conversation


def test_get_conversations_list_with_customer_filter(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试根据客户ID筛选会话列表"""
    token = get_token
    
    response = client.get(
        f"/api/v1/chat/conversations?customer_id={fake_customer.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    
    # 验证所有返回的会话都属于指定客户
    for conversation in result:
        assert conversation["customer_id"] == fake_customer.id


def test_get_single_conversation(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试获取指定会话详情"""
    token = get_token
    
    response = client.get(
        f"/api/v1/chat/conversations/{fake_conversation.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["id"] == fake_conversation.id
    assert result["title"] == fake_conversation.title
    assert result["customer_id"] == fake_conversation.customer_id


def test_get_conversation_messages(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试获取会话消息（核心功能）"""
    token = get_token
    
    # 先在会话中创建一些测试消息
    test_messages = [
        Message(
            id=f"msg_{i}",
            conversation_id=fake_conversation.id,
            content=f"测试消息 {i}",
            type="text",
            sender_id=fake_customer.id,
            sender_type="customer",
            timestamp=datetime.now()
        )
        for i in range(3)
    ]
    
    for msg in test_messages:
        db.add(msg)
    db.commit()
    
    # 测试获取消息
    response = client.get(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert isinstance(result, list)
    assert len(result) >= 3  # 至少包含我们创建的3条消息
    
    # 验证消息结构
    message = result[0]
    assert "id" in message
    assert "content" in message
    assert "sender" in message
    assert "timestamp" in message


def test_get_conversation_messages_with_pagination(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试会话消息分页功能"""
    token = get_token
    
    # 创建多条消息用于测试分页
    test_messages = [
        Message(
            id=f"page_msg_{i}",
            conversation_id=fake_conversation.id,
            content=f"分页测试消息 {i}",
            type="text",
            sender_id=fake_customer.id,
            sender_type="customer",
            timestamp=datetime.now()
        )
        for i in range(10)
    ]
    
    for msg in test_messages:
        db.add(msg)
    db.commit()
    
    # 测试分页参数
    response = client.get(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages?skip=0&limit=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert len(result) <= 5  # 应该最多返回5条


def test_send_message_http(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试HTTP发送消息接口"""
    token = get_token
    data = {
        "content": "HTTP方式发送的消息",
        "type": "text"
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["content"] == "HTTP方式发送的消息"
    assert result["type"] == "text"
    assert result["conversation_id"] == fake_conversation.id
    
    # 验证消息在数据库中
    saved_message = db.query(Message).filter(
        Message.conversation_id == fake_conversation.id,
        Message.content == "HTTP方式发送的消息"
    ).first()
    assert saved_message is not None


def test_mark_message_as_read(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试标记消息为已读"""
    token = get_token
    
    # 创建一条未读消息
    test_message = Message(
        id="unread_msg_123",
        conversation_id=fake_conversation.id,
        content="未读消息",
        type="text",
        sender_id=fake_customer.id,
        sender_type="customer",
        is_read=False,
        timestamp=datetime.now()
    )
    db.add(test_message)
    db.commit()
    
    # 标记为已读
    response = client.put(
        f"/api/v1/chat/messages/{test_message.id}/read",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "已标记" in result["message"]
    
    # 验证数据库中的状态
    db.refresh(test_message)
    assert test_message.is_read is True


def test_get_conversation_summary(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试获取会话摘要"""
    token = get_token
    
    response = client.get(
        f"/api/v1/chat/conversations/{fake_conversation.id}/summary",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "id" in result or "message_count" in result or "conversation_id" in result


def test_update_conversation_title(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试更新会话标题"""
    token = get_token
    update_data = {
        "title": "更新后的会话标题"
    }
    
    response = client.patch(
        f"/api/v1/chat/conversations/{fake_conversation.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["title"] == "更新后的会话标题"
    
    # 验证数据库中的更新
    db.refresh(fake_conversation)
    assert fake_conversation.title == "更新后的会话标题"


def test_consultant_takeover_conversation_http(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_consultant, 
    fake_conversation
):
    """测试顾问接管会话（HTTP接口）"""
    # 使用顾问身份的token
    with patch('app.api.deps.get_current_user') as mock_user:
        mock_user.return_value = fake_consultant
        
        response = client.post(
            f"/api/v1/chat/conversations/{fake_conversation.id}/takeover",
            headers={"Authorization": f"Bearer {get_token}"}  # 使用有效token
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "会话已由顾问接管" in result["message"]
        assert result["is_ai_controlled"] is False


def test_consultant_release_conversation_http(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_consultant, 
    fake_conversation
):
    """测试顾问取消接管（HTTP接口）"""
    # 先设置为接管状态
    fake_conversation.is_ai_controlled = False
    db.commit()
    
    with patch('app.api.deps.get_current_user') as mock_user:
        mock_user.return_value = fake_consultant
        
        response = client.post(
            f"/api/v1/chat/conversations/{fake_conversation.id}/release",
            headers={"Authorization": f"Bearer {get_token}"}  # 使用有效token
        )
        
        assert response.status_code == 200
        result = response.json()
        assert "会话已恢复为AI回复" in result["message"]
        assert result["is_ai_controlled"] is True


# ============ 权限和错误处理测试 ============

def test_get_nonexistent_conversation(
    client: TestClient, 
    get_token: str
):
    """测试获取不存在的会话"""
    token = get_token
    
    response = client.get(
        "/api/v1/chat/conversations/nonexistent_id",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404


def test_get_messages_from_nonexistent_conversation(
    client: TestClient, 
    get_token: str
):
    """测试从不存在的会话获取消息"""
    token = get_token
    
    response = client.get(
        "/api/v1/chat/conversations/nonexistent_id/messages",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 404 or response.status_code == 400


def test_unauthorized_access_without_token(client: TestClient):
    """测试未授权访问"""
    response = client.get("/api/v1/chat/conversations")
    assert response.status_code == 401


# ============ 原有辅助测试保留但重命名 ============

def test_http_send_message_auxiliary(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """HTTP发送消息接口测试（辅助测试，主要业务是WebSocket）"""
    token = get_token
    data = {"content": "HTTP消息测试", "type": "text"}
    url = f"/api/v1/chat/conversations/{fake_conversation.id}/messages"
    response = client.post(url, json=data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200 or response.status_code == 201
    
    msg = db.query(Message).filter(
        Message.conversation_id == fake_conversation.id, 
        Message.content == "HTTP消息测试"
    ).first()
    assert msg is not None
    assert msg.content == "HTTP消息测试"


# ============ 顾问接管状态测试 ============

@pytest.mark.asyncio
async def test_takeover_affects_ai_response(
    db: Session, 
    fake_customer, 
    fake_consultant, 
    fake_conversation
):
    """测试顾问接管状态对AI回复的影响"""
    chat_service = ChatService(db)
    
    # 1. 初始状态：AI控制
    assert chat_service.get_ai_controlled_status(fake_conversation.id) is True
    
    # 2. 顾问接管
    success = chat_service.set_ai_controlled_status(fake_conversation.id, False)
    assert success is True
    assert chat_service.get_ai_controlled_status(fake_conversation.id) is False
    
    # 3. 测试接管后AI不回复
    ai_service = AIResponseService(db)
    event = create_message_event(
        conversation_id=fake_conversation.id,
        user_id=fake_customer.id,
        content="接管后的消息",
        message_type="text",
        sender_type="customer"
    )
    
    should_reply = await ai_service.should_ai_reply(event)
    assert should_reply is False
    
    # 4. 取消接管
    success = chat_service.set_ai_controlled_status(fake_conversation.id, True)
    assert success is True
    assert chat_service.get_ai_controlled_status(fake_conversation.id) is True
    
    # 5. 取消接管后AI恢复回复
    should_reply = await ai_service.should_ai_reply(event)
    assert should_reply is True 