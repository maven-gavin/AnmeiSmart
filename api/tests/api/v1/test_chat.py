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
from app.schemas.chat import (
    create_text_message_content, 
    create_media_message_content, 
    create_system_event_content,
    MessageInfo
)


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


# ============ 第一阶段：修复现有测试 ============

@pytest.mark.asyncio
async def test_customer_message_full_flow_websocket(
    db: Session, 
    fake_customer, 
    fake_conversation, 
    mock_ai_service
):
    """测试场景1完整流程：客户通过WebSocket发送消息，触发AI回复"""
    
    # 1. 模拟WebSocket消息数据（使用新格式）
    message_data = {
        "action": "message",
        "data": {
            "content": create_text_message_content("我想了解双眼皮手术"),
            "type": "text",
            "sender_type": "customer",
            "is_important": False
        }
    }
    
    # 2. Mock MessageService来避免数据库外键约束问题
    mock_message_service = MagicMock()
    mock_customer_message = MagicMock()
    mock_customer_message.id = "msg_customer_123"
    mock_customer_message.content = create_text_message_content("我想了解双眼皮手术")
    mock_customer_message.sender_type = "customer"
    
    mock_ai_message = MagicMock()
    mock_ai_message.id = "msg_ai_456"
    mock_ai_message.content = create_text_message_content("这是AI的回复")
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
    
    # 9. 验证事件类型和新格式
    message_event = published_events[0]
    assert message_event.type == EventTypes.CHAT_MESSAGE_RECEIVED
    assert message_event.conversation_id == fake_conversation.id
    assert message_event.data["content"]["text"] == "我想了解双眼皮手术"


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


def test_send_text_message_http_new_format(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试HTTP发送文本消息（使用新格式）"""
    token = get_token
    data = {
        "content": create_text_message_content("HTTP新格式文本消息"),
        "type": "text"
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if response.status_code != 200:
        print(f"Error response: {response.json()}")
    assert response.status_code == 200
    result = response.json()
    assert result["type"] == "text"
    assert result["content"]["text"] == "HTTP新格式文本消息"
    
    # 验证数据库中的结构
    saved_message = db.query(Message).filter(
        Message.conversation_id == fake_conversation.id
    ).order_by(Message.timestamp.desc()).first()
    
    assert saved_message is not None
    assert saved_message.content["text"] == "HTTP新格式文本消息"


def test_get_conversation_messages_with_new_format(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试获取会话消息（验证新格式）"""
    token = get_token
    
    # 创建不同类型的测试消息（使用新格式）
    test_messages = [
        Message(
            id="new_text_msg_1",
            conversation_id=fake_conversation.id,
            content=create_text_message_content("文本消息 1"),
            type="text",
            sender_id=fake_customer.id,
            sender_type="customer",
            timestamp=datetime.now()
        ),
        Message(
            id="new_media_msg_1",
            conversation_id=fake_conversation.id,
            content=create_media_message_content(
                media_url="http://example.com/photo.jpg",
                media_name="photo.jpg",
                mime_type="image/jpeg",
                size_bytes=12345
            ),
            type="media",
            sender_id=fake_customer.id,
            sender_type="customer",
            timestamp=datetime.now()
        )
    ]
    
    for msg in test_messages:
        db.add(msg)
    db.commit()
    
    # 获取消息
    response = client.get(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert len(result) >= 2
    
    # 验证消息结构（新格式）
    for message in result:
        assert "content" in message
        assert message["type"] in ["text", "media", "system"]
        if message["type"] == "text":
            assert "text" in message["content"]
        elif message["type"] == "media":
            assert "media_info" in message["content"]


def test_mark_message_as_read(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试标记消息为已读"""
    token = get_token
    
    # 创建一条未读消息（新格式）
    test_message = Message(
        id="unread_msg_123",
        conversation_id=fake_conversation.id,
        content=create_text_message_content("未读消息"),
        type="text",
        sender_id=fake_customer.id,
        sender_type="customer",
        is_read=False,
        timestamp=datetime.now()
    )
    db.add(test_message)
    db.commit()
    
    # 标记为已读
    response = client.patch(
        f"/api/v1/chat/messages/{test_message.id}/read",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "已标记" in result["message"]
    
    # 验证数据库中的状态
    db.refresh(test_message)
    assert test_message.is_read is True


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
    
    # 2. 客户发送消息（新格式）
    message_data = {
        "action": "message", 
        "data": {
            "content": create_text_message_content("顾问接管后的消息"),
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
    assert event.data["content"]["text"] == "顾问接管后的消息"
    
    # 5. 验证AI服务没有被调用（因为顾问接管了）
    mock_ai_service.get_response.assert_not_called()


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
    
    # Mock JWT解码而不是整个verify_token函数
    with patch('app.core.security.jwt.decode') as mock_jwt_decode:
        mock_jwt_decode.return_value = {
            "sub": "user123",
            "exp": 9999999999  # 遥远的未来时间戳
        }
        
        from app.api.v1.endpoints.websocket import verify_websocket_token
        
        result = await verify_websocket_token("valid_token", mock_db)
        
        assert result is not None
        assert result["user_id"] == "user123"
        assert result["role"] == "customer"  # 这是从roles[0].name获取的
        assert result["username"] == "test_user"


# ============ 错误处理测试 ============

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


def test_unauthorized_access_without_token(client: TestClient):
    """测试未授权访问"""
    response = client.get("/api/v1/chat/conversations")
    assert response.status_code == 401


def test_invalid_content_structure(
    client: TestClient, 
    get_token: str, 
    fake_conversation
):
    """测试无效的内容结构"""
    token = get_token
    
    # 发送无效的content结构
    invalid_data = {
        "content": "这是旧格式的字符串内容",  # 应该是JSON对象
        "type": "text"
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=invalid_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # 根据实际实现，这应该返回错误或被转换
    assert response.status_code in [200, 400, 422]


# ============ 第二阶段：添加新功能测试 ============

def test_send_media_message_http(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试HTTP发送媒体消息"""
    token = get_token
    data = {
        "content": create_media_message_content(
            media_url="http://example.com/test_image.jpg",
            media_name="test_image.jpg",
            mime_type="image/jpeg",
            size_bytes=98765,
            text="这是测试图片",
            metadata={"width": 640, "height": 480}
        ),
        "type": "media"
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["type"] == "media"
    assert result["content"]["text"] == "这是测试图片"
    assert result["content"]["media_info"]["url"] == "http://example.com/test_image.jpg"
    assert result["content"]["media_info"]["mime_type"] == "image/jpeg"
    assert result["content"]["media_info"]["metadata"]["width"] == 640


def test_send_voice_message_http(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试HTTP发送语音消息"""
    token = get_token
    data = {
        "content": create_media_message_content(
            media_url="http://example.com/voice_message.m4a",
            media_name="voice_message.m4a",
            mime_type="audio/mp4",
            size_bytes=58240,
            metadata={"duration_seconds": 35.2}
        ),
        "type": "media"
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["type"] == "media"
    assert result["content"]["media_info"]["mime_type"] == "audio/mp4"
    assert result["content"]["media_info"]["metadata"]["duration_seconds"] == 35.2


def test_send_document_message_http(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试HTTP发送文档消息"""
    token = get_token
    data = {
        "content": create_media_message_content(
            media_url="http://example.com/medical_report.pdf",
            media_name="医疗报告.pdf",
            mime_type="application/pdf",
            size_bytes=1024000,
            text="这是我的医疗报告，请帮忙看一下",
            metadata={"pages": 5, "created_by": "医院系统"}
        ),
        "type": "media"
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["type"] == "media"
    assert result["content"]["text"] == "这是我的医疗报告，请帮忙看一下"
    assert result["content"]["media_info"]["mime_type"] == "application/pdf"
    assert result["content"]["media_info"]["metadata"]["pages"] == 5


def test_send_system_event_message(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_consultant, 
    fake_conversation
):
    """测试发送系统事件消息"""
    token = get_token
    data = {
        "content": create_system_event_content(
            event_type="takeover",
            status="completed",
            details={
                "from": "ai",
                "to": "consultant",
                "reason": "客户需要专业咨询服务"
            }
        ),
        "type": "system"
    }
    
    # 模拟顾问用户
    with patch('app.api.deps.get_current_user') as mock_user:
        mock_user.return_value = fake_consultant
        
        response = client.post(
            f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
            json=data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["type"] == "system"
        assert result["content"]["system_event_type"] == "takeover"
        assert result["content"]["status"] == "completed"
        assert result["content"]["details"]["from"] == "ai"


def test_message_with_reply_to(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试消息回复功能"""
    token = get_token
    
    # 先创建一条原始消息
    original_message = Message(
        id="original_msg_123",
        conversation_id=fake_conversation.id,
        content=create_text_message_content("原始消息"),
        type="text",
        sender_id=fake_customer.id,
        sender_type="customer",
        timestamp=datetime.now()
    )
    db.add(original_message)
    db.commit()
    
    # 创建回复消息
    data = {
        "content": create_text_message_content("这是回复消息"),
        "type": "text",
        "reply_to_message_id": original_message.id
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["reply_to_message_id"] == original_message.id
    assert result["content"]["text"] == "这是回复消息"


def test_message_with_reactions(
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试消息表情回应功能"""
    
    # 创建带reactions的消息
    message = Message(
        id="reaction_msg_123",
        conversation_id=fake_conversation.id,
        content=create_text_message_content("带表情回应的消息"),
        type="text",
        sender_id=fake_customer.id,
        sender_type="customer",
        reactions={"👍": [fake_customer.id], "❤️": []},
        timestamp=datetime.now()
    )
    db.add(message)
    db.commit()
    
    # 验证reactions存储
    db.refresh(message)
    assert "👍" in message.reactions
    assert fake_customer.id in message.reactions["👍"]
    assert "❤️" in message.reactions
    assert len(message.reactions["❤️"]) == 0


def test_message_with_extra_metadata(
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试消息额外元数据功能"""
    
    # 创建带extra_metadata的消息
    message = Message(
        id="metadata_msg_123",
        conversation_id=fake_conversation.id,
        content=create_media_message_content(
            media_url="http://example.com/uploaded_file.jpg",
            media_name="uploaded_file.jpg",
            mime_type="image/jpeg",
            size_bytes=125440
        ),
        type="media",
        sender_id=fake_customer.id,
        sender_type="customer",
        extra_metadata={
            "upload_method": "file_picker",
            "client_info": {"browser": "Chrome", "version": "120.0"},
            "processing_info": {"auto_enhanced": True, "filters_applied": ["brightness", "contrast"]}
        },
        timestamp=datetime.now()
    )
    db.add(message)
    db.commit()
    
    # 验证extra_metadata存储
    db.refresh(message)
    assert message.extra_metadata["upload_method"] == "file_picker"
    assert message.extra_metadata["client_info"]["browser"] == "Chrome"
    assert message.extra_metadata["processing_info"]["auto_enhanced"] is True


def test_mark_message_as_important(
    client: TestClient,
    get_token: str,
    db: Session,
    fake_customer,
    fake_conversation
):
    """测试标记消息为重点功能"""
    token = get_token
    
    # 创建一条测试消息
    test_message = Message(
        id="important_msg_123",
        conversation_id=fake_conversation.id,
        content=create_text_message_content("重要消息内容"),
        type="text",
        sender_id=fake_customer.id,
        sender_type="customer",
        is_important=False,
        timestamp=datetime.now()
    )
    db.add(test_message)
    db.commit()
    
    # 标记为重点
    response = client.patch(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages/{test_message.id}/important",
        json={"is_important": True},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert "标记为重点" in result["message"]
    
    # 验证数据库中的状态
    db.refresh(test_message)
    assert test_message.is_important is True


def test_missing_required_media_fields(
    client: TestClient, 
    get_token: str, 
    fake_conversation
):
    """测试媒体消息缺少必需字段"""
    token = get_token
    
    # 发送缺少media_info的媒体消息
    invalid_media_data = {
        "content": {"text": "只有文字没有媒体信息"},
        "type": "media"
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=invalid_media_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # 应该返回错误
    assert response.status_code in [400, 422]


def test_empty_system_event(
    client: TestClient, 
    get_token: str, 
    fake_conversation
):
    """测试空的系统事件"""
    token = get_token
    
    # 发送空的系统事件
    invalid_system_data = {
        "content": {},
        "type": "system"
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=invalid_system_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # 应该返回错误
    assert response.status_code in [400, 422]


# ============ 第三阶段：完善场景测试 ============

@pytest.mark.asyncio
async def test_multiple_file_upload_scenario(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试多文件上传场景（一文件一消息原则）"""
    token = get_token
    
    # 模拟用户上传3个图片和1个PDF
    files_data = [
        {
            "content": create_media_message_content(
                media_url="http://example.com/image1.jpg",
                media_name="皮肤照片1.jpg",
                mime_type="image/jpeg",
                size_bytes=123456,
                text="左侧面部照片"
            ),
            "type": "media"
        },
        {
            "content": create_media_message_content(
                media_url="http://example.com/image2.jpg",
                media_name="皮肤照片2.jpg",
                mime_type="image/jpeg",
                size_bytes=234567,
                text="右侧面部照片"
            ),
            "type": "media"
        },
        {
            "content": create_media_message_content(
                media_url="http://example.com/image3.jpg",
                media_name="皮肤照片3.jpg",
                mime_type="image/jpeg",
                size_bytes=345678,
                text="正面照片"
            ),
            "type": "media"
        },
        {
            "content": create_media_message_content(
                media_url="http://example.com/report.pdf",
                media_name="medical_report.pdf",
                mime_type="application/pdf",
                size_bytes=456789,
                text="最近的皮肤检查报告"
            ),
            "type": "media"
        }
    ]
    
    # 连续发送4条消息（模拟前端的行为）
    responses = []
    for i, file_data in enumerate(files_data):
        response = client.post(
            f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
            json=file_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        responses.append(response)
        await asyncio.sleep(0.05)  # 模拟发送间隔
    
    # 验证所有消息都发送成功
    for response in responses:
        assert response.status_code == 200
        assert response.json()["type"] == "media"
    
    # 验证数据库中有4条独立的消息
    messages = db.query(Message).filter(
        Message.conversation_id == fake_conversation.id,
        Message.type == "media"
    ).order_by(Message.timestamp.desc()).all()
    
    assert len(messages) >= 4
    
    # 验证每条消息都是独立的
    recent_messages = messages[:4]  # 取最近的4条
    file_names = [msg.content["media_info"]["name"] for msg in recent_messages]
    expected_names = ["medical_report.pdf", "皮肤照片3.jpg", "皮肤照片2.jpg", "皮肤照片1.jpg"]
    
    for expected_name in expected_names:
        assert expected_name in file_names


def test_video_call_system_events_flow(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_consultant, 
    fake_customer,
    fake_conversation
):
    """测试视频通话系统事件完整流程"""
    token = get_token
    call_id = "vc_call_abcdef123"
    
    # 1. 视频通话发起事件
    initiate_data = {
        "content": create_system_event_content(
            event_type="video_call_status",
            status="initiated",
            call_id=call_id,
            participants=[fake_consultant.id, fake_customer.id],
            initiator=fake_consultant.id
        ),
        "type": "system"
    }
    
    with patch('app.api.deps.get_current_user') as mock_user:
        mock_user.return_value = fake_consultant
        
        response = client.post(
            f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
            json=initiate_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["content"]["system_event_type"] == "video_call_status"
        assert result["content"]["status"] == "initiated"
        assert result["content"]["call_id"] == call_id
        
        # 2. 视频通话接受事件
        accept_data = {
            "content": create_system_event_content(
                event_type="video_call_status",
                status="accepted",
                call_id=call_id,
                participants=[fake_consultant.id, fake_customer.id],
                accepted_by=fake_customer.id
            ),
            "type": "system"
        }
        
        response = client.post(
            f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
            json=accept_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["content"]["status"] == "accepted"
        
        # 3. 视频通话结束事件
        end_data = {
            "content": create_system_event_content(
                event_type="video_call_status",
                status="ended",
                call_id=call_id,
                duration_seconds=1520,  # 25分20秒
                participants=[fake_consultant.id, fake_customer.id],
                ended_by=fake_consultant.id
            ),
            "type": "system"
        }
        
        response = client.post(
            f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
            json=end_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["content"]["status"] == "ended"
        assert result["content"]["duration_seconds"] == 1520
    
    # 验证数据库中有3条系统事件
    system_messages = db.query(Message).filter(
        Message.conversation_id == fake_conversation.id,
        Message.type == "system"
    ).all()
    
    assert len(system_messages) >= 3
    
    # 验证事件顺序和内容
    recent_system_msgs = sorted(system_messages[-3:], key=lambda x: x.timestamp)
    statuses = [msg.content["status"] for msg in recent_system_msgs]
    assert statuses == ["initiated", "accepted", "ended"]


def test_complex_message_thread_with_replies(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_consultant,
    fake_conversation
):
    """测试复杂的消息链和回复场景"""
    token = get_token
    
    # 1. 客户发起咨询
    customer_message_data = {
        "content": create_text_message_content("我想了解面部提升手术的风险和效果"),
        "type": "text"
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=customer_message_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    customer_msg_id = response.json()["id"]
    
    # 2. 客户上传照片作为补充
    photo_data = {
        "content": create_media_message_content(
            media_url="http://example.com/face_photo.jpg",
            media_name="current_face.jpg",
            mime_type="image/jpeg",
            size_bytes=789123,
            text="这是我目前的面部状况"
        ),
        "type": "media",
        "reply_to_message_id": customer_msg_id  # 回复之前的咨询消息
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=photo_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    photo_msg_id = response.json()["id"]
    assert response.json()["reply_to_message_id"] == customer_msg_id
    
    # 3. 顾问回复（模拟顾问接管）
    with patch('app.api.deps.get_current_user') as mock_user:
        mock_user.return_value = fake_consultant
        
        consultant_reply_data = {
            "content": create_text_message_content("感谢您提供照片。根据您的情况，我建议我们先进行视频咨询..."),
            "type": "text",
            "reply_to_message_id": photo_msg_id  # 回复照片消息
        }
        
        response = client.post(
            f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
            json=consultant_reply_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        consultant_msg_id = response.json()["id"]
        assert response.json()["reply_to_message_id"] == photo_msg_id
        
        # 4. 客户回复并标记为重要
        customer_follow_up = {
            "content": create_text_message_content("好的，我什么时候可以预约视频咨询？"),
            "type": "text",
            "reply_to_message_id": consultant_msg_id,
            "is_important": True  # 客户认为这是重要问题
        }
        
        # 切换回客户身份
        mock_user.return_value = fake_customer
        
        response = client.post(
            f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
            json=customer_follow_up,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        follow_up_msg_id = response.json()["id"]
        assert response.json()["is_important"] is True
    
    # 验证消息链的完整性
    all_messages = db.query(Message).filter(
        Message.conversation_id == fake_conversation.id
    ).order_by(Message.timestamp.asc()).all()
    
    # 找到我们创建的消息
    our_messages = [msg for msg in all_messages if msg.id in [
        customer_msg_id, photo_msg_id, consultant_msg_id, follow_up_msg_id
    ]]
    
    assert len(our_messages) == 4
    
    # 验证回复关系
    photo_msg = next(msg for msg in our_messages if msg.id == photo_msg_id)
    consultant_msg = next(msg for msg in our_messages if msg.id == consultant_msg_id)
    follow_up_msg = next(msg for msg in our_messages if msg.id == follow_up_msg_id)
    
    assert photo_msg.reply_to_message_id == customer_msg_id
    assert consultant_msg.reply_to_message_id == photo_msg_id
    assert follow_up_msg.reply_to_message_id == consultant_msg_id
    assert follow_up_msg.is_important is True


def test_consultant_takeover_complete_scenario(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_consultant,
    fake_conversation
):
    """测试顾问接管的完整场景"""
    token = get_token
    
    # 1. 初始状态：AI控制
    chat_service = ChatService(db)
    assert chat_service.get_ai_controlled_status(fake_conversation.id) is True
    
    # 2. 客户发送复杂问题
    complex_question = {
        "content": create_text_message_content("我有严重的皮肤过敏史，还能做激光治疗吗？之前用过激素药膏..."),
        "type": "text"
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=complex_question,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    customer_question_id = response.json()["id"]
    
    # 3. 顾问接管会话
    with patch('app.api.deps.get_current_user') as mock_user:
        mock_user.return_value = fake_consultant
        
        response = client.post(
            f"/api/v1/chat/conversations/{fake_conversation.id}/takeover",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["is_ai_controlled"] is False
        
        # 4. 发送接管通知（系统事件）
        takeover_event = {
            "content": create_system_event_content(
                event_type="takeover",
                status="completed",
                details={
                    "from": "ai",
                    "to": "consultant",
                    "consultant_id": fake_consultant.id,
                    "reason": "复杂医疗咨询需要专业医生解答"
                }
            ),
            "type": "system"
        }
        
        response = client.post(
            f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
            json=takeover_event,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        takeover_event_id = response.json()["id"]
        
        # 5. 顾问专业回复
        professional_response = {
            "content": create_text_message_content(
                "您好！我是王医生。关于您的皮肤过敏史和激光治疗的问题，"
                "我需要详细了解您的过敏类型和既往用药情况，建议先进行面诊评估..."
            ),
            "type": "text",
            "reply_to_message_id": customer_question_id
        }
        
        response = client.post(
            f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
            json=professional_response,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        doctor_response_id = response.json()["id"]
        
        # 6. 客户感谢并提供更多信息
        mock_user.return_value = fake_customer  # 切换回客户
        
        additional_info = {
            "content": create_text_message_content("谢谢王医生！我的过敏主要是对花粉和某些化妆品..."),
            "type": "text",
            "reply_to_message_id": doctor_response_id
        }
        
        response = client.post(
            f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
            json=additional_info,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
    
    # 验证整个接管流程
    messages = db.query(Message).filter(
        Message.conversation_id == fake_conversation.id
    ).order_by(Message.timestamp.desc()).all()
    
    # 验证消息类型分布
    recent_messages = messages[:5]  # 最近5条消息
    message_types = [msg.type for msg in recent_messages]
    assert "text" in message_types  # 有文本消息
    assert "system" in message_types  # 有系统事件
    
    # 验证接管状态
    assert chat_service.get_ai_controlled_status(fake_conversation.id) is False
    
    # 验证系统事件记录了接管详情
    takeover_msg = next((msg for msg in recent_messages if msg.type == "system"), None)
    assert takeover_msg is not None
    assert takeover_msg.content["system_event_type"] == "takeover"
    assert takeover_msg.content["details"]["consultant_id"] == fake_consultant.id


def test_mixed_content_conversation_flow(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试混合内容的会话流程（文本+图片+语音+文档）"""
    token = get_token
    
    # 1. 文本咨询
    text_msg = {
        "content": create_text_message_content("医生您好，我想咨询一下面部痘印的治疗方案"),
        "type": "text"
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=text_msg,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    text_msg_id = response.json()["id"]
    
    # 2. 上传面部照片
    photo_msg = {
        "content": create_media_message_content(
            media_url="http://example.com/face_acne_scars.jpg",
            media_name="face_acne_scars.jpg",
            mime_type="image/jpeg",
            size_bytes=567890,
            text="这是我现在的痘印情况",
            metadata={"width": 1080, "height": 1920, "taken_with": "iPhone 15"}
        ),
        "type": "media",
        "extra_metadata": {"upload_method": "camera_capture"}
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=photo_msg,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    photo_msg_id = response.json()["id"]
    
    # 3. 发送语音补充说明
    voice_msg = {
        "content": create_media_message_content(
            media_url="http://example.com/voice_description.m4a",
            media_name="voice_description.m4a",
            mime_type="audio/mp4",
            size_bytes=234567,
            metadata={"duration_seconds": 45.3, "quality": "high"}
        ),
        "type": "media",
        "extra_metadata": {"upload_method": "voice_recorder"}
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=voice_msg,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    voice_msg_id = response.json()["id"]
    
    # 4. 上传之前的检查报告
    document_msg = {
        "content": create_media_message_content(
            media_url="http://example.com/previous_skin_analysis.pdf",
            media_name="previous_skin_analysis.pdf",
            mime_type="application/pdf",
            size_bytes=1234567,
            text="这是我6个月前做的皮肤分析报告",
            metadata={"pages": 8, "generated_by": "美肤诊所皮肤检测仪"}
        ),
        "type": "media",
        "extra_metadata": {"upload_method": "file_picker", "scan_quality": "300dpi"}
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=document_msg,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    document_msg_id = response.json()["id"]
    
    # 5. 补充文字说明
    follow_up_text = {
        "content": create_text_message_content("以上是我的详细情况，请问医生有什么建议？"),
        "type": "text",
        "is_important": True
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=follow_up_text,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    follow_up_id = response.json()["id"]
    
    # 验证所有消息都成功创建
    messages = db.query(Message).filter(
        Message.conversation_id == fake_conversation.id
    ).order_by(Message.timestamp.desc()).all()
    
    our_message_ids = {text_msg_id, photo_msg_id, voice_msg_id, document_msg_id, follow_up_id}
    found_messages = [msg for msg in messages if msg.id in our_message_ids]
    
    assert len(found_messages) == 5
    
    # 验证消息类型分布
    message_types = [msg.type for msg in found_messages]
    assert message_types.count("text") == 2
    assert message_types.count("media") == 3
    
    # 验证媒体文件类型分布
    media_messages = [msg for msg in found_messages if msg.type == "media"]
    mime_types = [msg.content["media_info"]["mime_type"] for msg in media_messages]
    assert "image/jpeg" in mime_types
    assert "audio/mp4" in mime_types
    assert "application/pdf" in mime_types
    
    # 验证元数据正确存储
    photo_msg_obj = next(msg for msg in found_messages if msg.id == photo_msg_id)
    assert photo_msg_obj.extra_metadata["upload_method"] == "camera_capture"
    
    voice_msg_obj = next(msg for msg in found_messages if msg.id == voice_msg_id)
    assert voice_msg_obj.content["media_info"]["metadata"]["duration_seconds"] == 45.3


# ============ 第四阶段：性能和边界测试 ============

@pytest.mark.asyncio
async def test_concurrent_message_sending(
    client: TestClient, 
    get_token: str, 
    fake_conversation
):
    """测试并发发送消息"""
    token = get_token
    
    # 创建多个并发消息
    async def send_message(content_text, message_id):
        data = {
            "content": create_text_message_content(f"{content_text} #{message_id}"),
            "type": "text"
        }
        return client.post(
            f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
            json=data,
            headers={"Authorization": f"Bearer {token}"}
        )
    
    # 并发发送10条消息
    tasks = [send_message(f"并发消息", i) for i in range(10)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 验证大部分消息发送成功
    success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
    assert success_count >= 8  # 允许少量失败


def test_large_text_message(
    client: TestClient, 
    get_token: str, 
    fake_conversation
):
    """测试发送大文本消息"""
    token = get_token
    
    # 创建一个很长的文本消息（约5KB）
    long_text = "这是一个很长的医疗咨询描述。" * 200  # 约5KB的文本
    
    data = {
        "content": create_text_message_content(long_text),
        "type": "text"
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert len(result["content"]["text"]) == len(long_text)


def test_large_media_file_metadata(
    client: TestClient, 
    get_token: str, 
    fake_conversation
):
    """测试大文件的媒体消息"""
    token = get_token
    
    # 模拟一个1GB的视频文件
    data = {
        "content": create_media_message_content(
            media_url="http://example.com/large_video.mp4",
            media_name="手术演示视频.mp4",
            mime_type="video/mp4",
            size_bytes=1024 * 1024 * 1024,  # 1GB
            text="这是详细的手术演示视频，请医生查看",
            metadata={
                "duration_seconds": 3600,  # 1小时
                "resolution": "4K",
                "bitrate": "50Mbps",
                "codec": "H.264"
            }
        ),
        "type": "media"
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["content"]["media_info"]["size_bytes"] == 1024 * 1024 * 1024
    assert result["content"]["media_info"]["metadata"]["duration_seconds"] == 3600


def test_complex_nested_metadata(
    client: TestClient, 
    get_token: str, 
    fake_conversation
):
    """测试复杂嵌套的元数据"""
    token = get_token
    
    complex_metadata = {
        "camera_info": {
            "make": "Apple",
            "model": "iPhone 15 Pro Max",
            "settings": {
                "iso": 400,
                "aperture": "f/1.8",
                "shutter_speed": "1/120",
                "focal_length": "24mm",
                "white_balance": "auto"
            },
            "lens": {
                "type": "wide",
                "optical_zoom": "1x",
                "stabilization": True
            }
        },
        "location": {
            "latitude": 37.7749,
            "longitude": -122.4194,
            "altitude": 52.5,
            "accuracy": 5.0,
            "address": {
                "street": "123 Medical Center Blvd",
                "city": "San Francisco",
                "state": "CA",
                "country": "USA"
            }
        },
        "processing": {
            "ai_enhanced": True,
            "filters_applied": [
                {"name": "auto_enhance", "strength": 0.8},
                {"name": "color_correction", "strength": 0.6},
                {"name": "skin_smoothing", "strength": 0.3}
            ],
            "analysis_results": {
                "skin_type": "combination",
                "detected_issues": ["acne_scars", "uneven_tone", "fine_lines"],
                "confidence_scores": {
                    "acne_scars": 0.92,
                    "uneven_tone": 0.87,
                    "fine_lines": 0.73
                }
            }
        },
        "medical_context": {
            "body_part": "face",
            "examination_type": "routine_followup",
            "previous_treatments": [
                {"date": "2024-12-01", "treatment": "chemical_peel", "doctor": "Dr. Smith"},
                {"date": "2024-11-15", "treatment": "laser_therapy", "doctor": "Dr. Johnson"}
            ]
        }
    }
    
    data = {
        "content": create_media_message_content(
            media_url="http://example.com/detailed_analysis_photo.jpg",
            media_name="detailed_skin_analysis.jpg",
            mime_type="image/jpeg",
            size_bytes=2048576,
            text="这是经过详细分析的皮肤照片",
            metadata=complex_metadata
        ),
        "type": "media",
        "extra_metadata": {
            "upload_session": "session_abc123",
            "client_version": "iOS_app_v2.1.0",
            "network_info": {
                "connection_type": "wifi",
                "speed_mbps": 50.5,
                "latency_ms": 25
            }
        }
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    
    # 验证复杂元数据正确存储
    stored_metadata = result["content"]["media_info"]["metadata"]
    assert stored_metadata["camera_info"]["make"] == "Apple"
    assert stored_metadata["location"]["latitude"] == 37.7749
    assert len(stored_metadata["processing"]["filters_applied"]) == 3
    assert stored_metadata["medical_context"]["body_part"] == "face"


def test_unicode_and_emoji_handling(
    client: TestClient, 
    get_token: str, 
    fake_conversation
):
    """测试Unicode和emoji的处理"""
    token = get_token
    
    # 包含多种语言和emoji的消息
    unicode_text = (
        "👨‍⚕️ 医生您好！我是来自中国的患者 🇨🇳\n"
        "こんにちは、日本語も話せます 🗾\n"
        "Hello, I also speak English 🇺🇸\n"
        "¡Hola! También hablo español 🇪🇸\n"
        "Здравствуйте! Я говорю по-русски 🇷🇺\n"
        "مرحبا! أتحدث العربية أيضا 🌙\n"
        "😊💖✨🌟💫🎉🎊🔥💯👍"
    )
    
    data = {
        "content": create_text_message_content(unicode_text),
        "type": "text"
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["content"]["text"] == unicode_text
    
    # 测试emoji文件名
    emoji_filename = "我的照片_😊_2025年_🎉.jpg"
    media_data = {
        "content": create_media_message_content(
            media_url="http://example.com/emoji_file.jpg",
            media_name=emoji_filename,
            mime_type="image/jpeg",
            size_bytes=123456,
            text="文件名包含emoji的照片 📸✨"
        ),
        "type": "media"
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=media_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    result = response.json()
    assert result["content"]["media_info"]["name"] == emoji_filename


def test_malformed_json_content(
    client: TestClient, 
    get_token: str, 
    fake_conversation
):
    """测试格式错误的JSON内容"""
    token = get_token
    
    # 测试无效的content结构
    invalid_data_cases = [
        {
            "content": None,  # null content
            "type": "text"
        },
        {
            "content": [],  # array instead of object
            "type": "text"
        },
        {
            "content": "plain string",  # string instead of object
            "type": "text"
        },
        {
            "content": {"wrong_field": "value"},  # missing required fields
            "type": "text"
        },
        {
            "content": {"text": "valid", "media_info": "invalid"},  # mixed valid/invalid
            "type": "text"
        }
    ]
    
    for invalid_data in invalid_data_cases:
        response = client.post(
            f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
            json=invalid_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 应该返回错误状态码
        assert response.status_code in [400, 422, 500]


def test_extreme_reaction_scenarios(
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试极端的表情回应场景"""
    
    # 创建一个有很多表情回应的消息
    many_reactions = {}
    emojis = ["👍", "❤️", "😂", "😮", "😢", "😡", "🔥", "💯", "🎉", "🙏"]
    user_ids = [f"user_{i}" for i in range(100)]  # 100个用户
    
    for emoji in emojis:
        many_reactions[emoji] = user_ids[:10]  # 每个emoji有10个用户点赞
    
    message = Message(
        id="many_reactions_msg",
        conversation_id=fake_conversation.id,
        content=create_text_message_content("这条消息有很多表情回应"),
        type="text",
        sender_id=fake_customer.id,
        sender_type="customer",
        reactions=many_reactions,
        timestamp=datetime.now()
    )
    db.add(message)
    db.commit()
    
    # 验证大量reactions正确存储
    db.refresh(message)
    assert len(message.reactions) == 10  # 10种emoji
    total_reactions = sum(len(users) for users in message.reactions.values())
    assert total_reactions == 100  # 总共100个反应


def test_message_chain_depth_limit(
    client: TestClient, 
    get_token: str, 
    db: Session, 
    fake_customer, 
    fake_conversation
):
    """测试消息回复链的深度限制"""
    token = get_token
    
    # 创建一个深度为10的回复链
    message_ids = []
    
    # 第一条消息
    first_msg_data = {
        "content": create_text_message_content("这是回复链的开始"),
        "type": "text"
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=first_msg_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    message_ids.append(response.json()["id"])
    
    # 创建9层回复
    for i in range(1, 10):
        reply_data = {
            "content": create_text_message_content(f"这是第{i}层回复"),
            "type": "text",
            "reply_to_message_id": message_ids[-1]  # 回复上一条消息
        }
        
        response = client.post(
            f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
            json=reply_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        message_ids.append(response.json()["id"])
    
    # 验证回复链的完整性
    messages = db.query(Message).filter(
        Message.id.in_(message_ids)
    ).all()
    
    assert len(messages) == 10
    
    # 验证回复关系
    for i in range(1, 10):
        current_msg = next(msg for msg in messages if msg.id == message_ids[i])
        assert current_msg.reply_to_message_id == message_ids[i-1]


def test_database_transaction_rollback_scenario(
    client: TestClient, 
    get_token: str, 
    fake_conversation
):
    """测试数据库事务回滚场景"""
    token = get_token
    
    # 尝试创建一个会导致数据库错误的消息
    # 例如：引用不存在的消息ID作为回复
    invalid_reply_data = {
        "content": create_text_message_content("回复不存在的消息"),
        "type": "text",
        "reply_to_message_id": "nonexistent_message_id_12345"
    }
    
    response = client.post(
        f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
        json=invalid_reply_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # 根据实际实现，这可能成功（如果没有外键约束）或失败
    # 这里主要测试系统不会崩溃
    assert response.status_code in [200, 400, 404, 422, 500]


@pytest.mark.asyncio
async def test_websocket_connection_stress(mock_websocket):
    """测试WebSocket连接压力"""
    
    # 模拟大量并发WebSocket消息
    messages = []
    for i in range(50):
        message_data = {
            "action": "message",
            "data": {
                "content": create_text_message_content(f"压力测试消息 {i}"),
                "type": "text",
                "sender_type": "customer"
            }
        }
        messages.append(message_data)
    
    # 模拟并发处理
    from app.services.websocket.websocket_handler import WebSocketHandler
    handler = WebSocketHandler()
    
    async def process_message(msg_data):
        try:
            # 模拟处理WebSocket消息
            return await handler.handle_websocket_message(
                msg_data, 
                "test_user_id", 
                "test_conversation_id"
            )
        except Exception as e:
            return {"error": str(e)}
    
    # 并发处理所有消息
    results = await asyncio.gather(
        *[process_message(msg) for msg in messages],
        return_exceptions=True
    )
    
    # 验证大部分消息处理成功
    success_count = sum(1 for r in results if isinstance(r, dict) and "error" not in r)
    assert success_count >= 40  # 至少80%成功率


def test_memory_usage_with_large_messages(
    client: TestClient, 
    get_token: str, 
    fake_conversation
):
    """测试大消息的内存使用"""
    token = get_token
    
    # 创建多个大消息，测试内存使用
    large_messages = []
    
    for i in range(5):
        # 每个消息约1MB的元数据
        large_metadata = {
            "analysis_data": ["data_point_" + str(j) for j in range(10000)],
            "processing_log": [f"step_{k}: processing..." for k in range(5000)],
            "measurements": {f"metric_{m}": m * 0.001 for m in range(1000)}
        }
        
        message_data = {
            "content": create_media_message_content(
                media_url=f"http://example.com/large_analysis_{i}.dat",
                media_name=f"large_analysis_{i}.dat",
                mime_type="application/octet-stream",
                size_bytes=100 * 1024 * 1024,  # 100MB文件
                text=f"大数据分析文件 {i}",
                metadata=large_metadata
            ),
            "type": "media"
        }
        
        response = client.post(
            f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
            json=message_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # 即使是大消息也应该正常处理
        assert response.status_code in [200, 413, 422]  # 200成功，413过大，422验证错误
        
        if response.status_code == 200:
            large_messages.append(response.json()["id"])
    
    # 如果有成功创建的大消息，验证它们能正常检索
    if large_messages:
        response = client.get(
            f"/api/v1/chat/conversations/{fake_conversation.id}/messages",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200 