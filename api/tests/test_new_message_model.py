"""
测试新的统一消息模型
"""
import pytest
import asyncio
from sqlalchemy.orm import Session
from app.services.chat.message_service import MessageService
from app.services.chat.chat_service import ChatService
from app.db.models.chat import Conversation, Message
from app.db.models.user import User
from app.schemas.chat import MessageInfo, ConversationInfo
from app.db.uuid_utils import conversation_id, message_id, user_id


class TestUnifiedMessageModel:
    """测试统一消息模型"""

    @pytest.fixture
    def message_service(self, db: Session):
        """创建消息服务实例"""
        return MessageService(db)

    @pytest.fixture
    def chat_service(self, db: Session):
        """创建聊天服务实例"""
        return ChatService(db)

    @pytest.fixture
    def test_conversation(self, db: Session):
        """创建测试会话"""
        customer_id = user_id()
        conv_id = conversation_id()
        
        # 创建测试客户
        customer = User(
            id=customer_id,
            username="测试客户",
            email="customer@test.com",
            password_hash="test_hash"
        )
        db.add(customer)
        
        # 创建测试会话
        conversation = Conversation(
            id=conv_id,
            title="测试会话",
            customer_id=customer_id,
            is_active=True,
            is_ai_controlled=True
        )
        db.add(conversation)
        db.commit()
        
        return conversation

    @pytest.mark.asyncio
    async def test_create_text_message(self, message_service: MessageService, test_conversation: Conversation):
        """测试创建文本消息"""
        # 使用新的便利方法创建文本消息
        message = await message_service.create_text_message(
            conversation_id=test_conversation.id,
            text="这是一条测试文本消息",
            sender_id="test_user",
            sender_type="customer"
        )
        
        assert message is not None
        assert message.type == "text"
        assert isinstance(message.content, dict)
        assert message.content["text"] == "这是一条测试文本消息"
        assert message.conversation_id == test_conversation.id

    @pytest.mark.asyncio
    async def test_create_media_message(self, message_service: MessageService, test_conversation: Conversation):
        """测试创建媒体消息"""
        # 使用新的便利方法创建媒体消息
        message = await message_service.create_media_message(
            conversation_id=test_conversation.id,
            media_url="https://example.com/image.jpg",
            media_name="test_image.jpg",
            mime_type="image/jpeg",
            size_bytes=1024,
            sender_id="test_user",
            sender_type="customer",
            text="这是图片的描述",
            metadata={"width": 800, "height": 600},
            upload_method="file_picker"
        )
        
        assert message is not None
        assert message.type == "media"
        assert isinstance(message.content, dict)
        assert message.content["text"] == "这是图片的描述"
        assert "media_info" in message.content
        
        media_info = message.content["media_info"]
        assert media_info["url"] == "https://example.com/image.jpg"
        assert media_info["name"] == "test_image.jpg"
        assert media_info["mime_type"] == "image/jpeg"
        assert media_info["size_bytes"] == 1024
        assert media_info["metadata"]["width"] == 800
        assert media_info["metadata"]["height"] == 600
        
        assert message.extra_metadata["upload_method"] == "file_picker"

    @pytest.mark.asyncio
    async def test_create_system_event_message(self, message_service: MessageService, test_conversation: Conversation):
        """测试创建系统事件消息"""
        # 使用新的便利方法创建系统事件消息
        message = await message_service.create_system_event_message(
            conversation_id=test_conversation.id,
            event_type="takeover",
            status="completed",
            sender_id="test_consultant",
            event_data={"consultant_name": "张医生"}
        )
        
        assert message is not None
        assert message.type == "system"
        assert isinstance(message.content, dict)
        assert message.content["system_event_type"] == "takeover"
        assert message.content["status"] == "completed"
        assert message.content["consultant_name"] == "张医生"

    @pytest.mark.asyncio
    async def test_backward_compatibility(self, message_service: MessageService, test_conversation: Conversation):
        """测试向后兼容性 - 原有的create_message方法仍然可用"""
        # 使用原有方法传入字符串内容
        message = await message_service.create_message(
            conversation_id=test_conversation.id,
            content="这是传统方式的消息",
            message_type="text",
            sender_id="test_user",
            sender_type="customer"
        )
        
        assert message is not None
        assert message.type == "text"
        assert isinstance(message.content, dict)
        assert message.content["text"] == "这是传统方式的消息"

    @pytest.mark.asyncio
    async def test_structured_content_direct(self, message_service: MessageService, test_conversation: Conversation):
        """测试直接传入结构化内容"""
        # 直接传入结构化内容对象
        structured_content = {
            "text": "这是结构化的文本消息",
            "metadata": {"custom_field": "custom_value"}
        }
        
        message = await message_service.create_message(
            conversation_id=test_conversation.id,
            content=structured_content,
            message_type="text",
            sender_id="test_user",
            sender_type="customer"
        )
        
        assert message is not None
        assert message.type == "text"
        assert message.content == structured_content

    @pytest.mark.asyncio
    async def test_chat_service_convenience_methods(self, chat_service: ChatService, test_conversation: Conversation):
        """测试ChatService的便利方法"""
        # 测试发送文本消息
        text_message = await chat_service.send_text_message(
            conversation_id=test_conversation.id,
            text="通过ChatService发送的文本消息",
            sender_id="test_user",
            sender_type="customer"
        )
        
        assert text_message is not None
        assert text_message.type == "text"
        
        # 测试发送媒体消息
        media_message = await chat_service.send_media_message(
            conversation_id=test_conversation.id,
            media_url="https://example.com/audio.mp3",
            media_name="test_audio.mp3",
            mime_type="audio/mpeg",
            size_bytes=2048,
            sender_id="test_user",
            sender_type="customer",
            text="这是语音消息",
            metadata={"duration_seconds": 30}
        )
        
        assert media_message is not None
        assert media_message.type == "media"
        
        # 测试发送系统事件消息
        system_message = await chat_service.send_system_event_message(
            conversation_id=test_conversation.id,
            event_type="user_joined",
            status="completed",
            event_data={"user_name": "新用户"}
        )
        
        assert system_message is not None
        assert system_message.type == "system"

    def test_message_schema_conversion(self, db: Session, test_conversation: Conversation):
        """测试MessageInfo schema的转换功能"""
        # 直接在数据库中创建新格式的消息
        msg_id = message_id()
        db_message = Message(
            id=msg_id,
            conversation_id=test_conversation.id,
            content={
                "text": "这是数据库中的消息",
                "extra_field": "额外字段"
            },
            type="text",
            sender_id="test_user",
            sender_type="customer",
            is_read=False,
            is_important=False,
            reactions={"👍": ["user1", "user2"]},
            extra_metadata={"source": "test"}
        )
        db.add(db_message)
        db.commit()
        
        # 使用schema转换
        message_info = MessageInfo.from_model(db_message)
        
        assert message_info is not None
        assert message_info.id == msg_id
        assert message_info.type == "text"
        assert message_info.content["text"] == "这是数据库中的消息"
        assert message_info.content["extra_field"] == "额外字段"
        assert message_info.reactions["👍"] == ["user1", "user2"]
        assert message_info.extra_metadata["source"] == "test"

    def test_message_convenience_properties(self, db: Session, test_conversation: Conversation):
        """测试MessageInfo的便利属性"""
        # 创建文本消息
        text_msg = Message(
            id=message_id(),
            conversation_id=test_conversation.id,
            content={"text": "文本消息内容"},
            type="text",
            sender_id="test_user",
            sender_type="customer"
        )
        db.add(text_msg)
        
        # 创建媒体消息
        media_msg = Message(
            id=message_id(),
            conversation_id=test_conversation.id,
            content={
                "text": "图片描述",
                "media_info": {
                    "url": "https://example.com/pic.jpg",
                    "name": "pic.jpg",
                    "mime_type": "image/jpeg",
                    "size_bytes": 1024,
                    "metadata": {"width": 800, "height": 600}
                }
            },
            type="media",
            sender_id="test_user",
            sender_type="customer"
        )
        db.add(media_msg)
        db.commit()
        
        # 测试文本消息的便利属性
        text_info = MessageInfo.from_model(text_msg)
        assert text_info.text_content == "文本消息内容"
        assert text_info.media_info is None
        
        # 测试媒体消息的便利属性
        media_info = MessageInfo.from_model(media_msg)
        assert media_info.text_content == "图片描述"
        assert media_info.media_info is not None
        assert media_info.media_info.url == "https://example.com/pic.jpg"
        assert media_info.media_info.metadata["width"] == 800

    def test_conversation_with_new_messages(self, db: Session, test_conversation: Conversation):
        """测试会话获取新格式消息"""
        message_service = MessageService(db)
        
        # 创建几条不同类型的消息
        messages_data = [
            {
                "content": {"text": "第一条文本消息"},
                "type": "text"
            },
            {
                "content": {
                    "text": "图片消息",
                    "media_info": {
                        "url": "https://example.com/img.jpg",
                        "name": "img.jpg",
                        "mime_type": "image/jpeg",
                        "size_bytes": 2048
                    }
                },
                "type": "media"
            },
            {
                "content": {
                    "system_event_type": "takeover",
                    "status": "completed"
                },
                "type": "system"
            }
        ]
        
        for msg_data in messages_data:
            db_message = Message(
                id=message_id(),
                conversation_id=test_conversation.id,
                content=msg_data["content"],
                type=msg_data["type"],
                sender_id="test_user",
                sender_type="customer"
            )
            db.add(db_message)
        
        db.commit()
        
        # 获取会话消息
        messages = message_service.get_conversation_messages(test_conversation.id)
        
        assert len(messages) == 3
        assert all(isinstance(msg, MessageInfo) for msg in messages)
        assert messages[0].type == "text"
        assert messages[1].type == "media"
        assert messages[2].type == "system" 