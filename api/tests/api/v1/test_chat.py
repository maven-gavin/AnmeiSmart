import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models.user import User
from app.db.models.chat import Conversation, Message
from app.services.chat.ai_response_service import AIResponseService
from app.services.chat.message_service import MessageService
from app.core.events import EventTypes
from app.api.deps import get_db
from app.core.websocket_manager import websocket_manager
from app.api.v1.endpoints.chat import get_user_role
import asyncio
from app.services import user_service as crud_user
from app.schemas.user import UserCreate
from app.services.chat.chat_service import ChatService

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
    conv = Conversation(title="test conv", customer_id=fake_customer.id)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

@pytest.mark.asyncio
async def test_message_save_and_broadcast(db: Session, fake_customer, fake_conversation):
    """测试消息保存与广播流程（单元测试）"""
    service = AIResponseService(db)
    # 构造事件
    event = type('Event', (), {})()
    event.conversation_id = fake_conversation.id
    event.user_id = fake_customer.id
    event.data = {
        "content": "你好，AI！",
        "message_type": "text",
        "sender_type": "customer",
        "is_important": False
    }
    # 调用
    await service.handle_message_event(event)
    # 检查消息是否保存
    msg = db.query(Message).filter(Message.conversation_id == fake_conversation.id).first()
    assert msg is not None
    assert msg.content == "你好，AI！"
    assert msg.sender_id == fake_customer.id
    # 检查事件是否发布（可用mock/patch event_bus）

@pytest.mark.asyncio
async def test_ai_reply_trigger(db: Session, fake_customer, fake_conversation):
    """测试AI回复是否被正确触发（单元测试）"""
    service = AIResponseService(db)
    # 先插入一条客户消息
    event = type('Event', (), {})()
    event.conversation_id = fake_conversation.id
    event.user_id = fake_customer.id
    event.data = {
        "content": "请问如何预约？",
        "message_type": "text",
        "sender_type": "customer",
        "is_important": False
    }
    await service.handle_message_event(event)
    # 检查AI回复是否入库（异步，需等待）
    await asyncio.sleep(1.5)  # 视AI服务mock速度调整
    ai_msg = db.query(Message).filter(Message.conversation_id == fake_conversation.id, Message.sender_type == "ai").first()
    assert ai_msg is not None
    assert "抱歉" in ai_msg.content or ai_msg.sender_type == "ai"

# 集成测试：WebSocket端到端（需依赖完整服务和WebSocket客户端模拟）
def test_http_send_message(client: TestClient, get_token: str, db: Session, fake_customer, fake_conversation):
    """测试HTTP发送消息接口"""
    token = get_token
    data = {"content": "HTTP消息测试", "type": "text"}
    url = f"/api/v1/chat/conversations/{fake_conversation.id}/messages"
    response = client.post(url, json=data, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200 or response.status_code == 201
    msg = db.query(Message).filter(Message.conversation_id == fake_conversation.id, Message.content == "HTTP消息测试").first()
    assert msg is not None
    assert msg.content == "HTTP消息测试"

# WebSocket集成测试建议：可用pytest-asyncio+websockets库实现，略。

@pytest.mark.asyncio
async def test_takeover_and_release_conversation(db: Session, fake_customer, fake_consultant, fake_conversation):
    """测试顾问接管与取消接管会话，is_ai_controlled状态变化"""
    service = ChatService(db)
    # 初始应为True
    assert service.get_ai_controlled_status(fake_conversation.id) is True
    # 顾问接管
    ok = service.set_ai_controlled_status(fake_conversation.id, False)
    assert ok is True
    assert service.get_ai_controlled_status(fake_conversation.id) is False
    # 顾问取消接管
    ok = service.set_ai_controlled_status(fake_conversation.id, True)
    assert ok is True
    assert service.get_ai_controlled_status(fake_conversation.id) is True 