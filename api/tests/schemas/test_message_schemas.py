import pytest
from datetime import datetime
from unittest.mock import MagicMock

from app.schemas.chat import (
    MessageInfo,
    ConversationInfo,
    create_text_message_content,
    create_media_message_content,
    create_system_event_content,
    MessageCreate
)


class TestMessageContentCreators:
    """测试消息内容创建函数"""
    
    def test_create_text_message_content_basic(self):
        """测试基本文本消息内容创建"""
        content = create_text_message_content("Hello world")
        assert content == {"text": "Hello world"}
        assert isinstance(content, dict)
    
    def test_create_media_message_content_full(self):
        """测试完整媒体消息内容创建"""
        content = create_media_message_content(
            media_url="https://example.com/image.jpg",
            media_name="image.jpg",
            mime_type="image/jpeg",
            size_bytes=123456,
            text="Image description",
            metadata={"width": 800, "height": 600}
        )
        
        expected = {
            "text": "Image description",
            "media_info": {
                "url": "https://example.com/image.jpg",
                "name": "image.jpg", 
                "mime_type": "image/jpeg",
                "size_bytes": 123456,
                "metadata": {"width": 800, "height": 600}
            }
        }
        assert content == expected
    
    def test_create_system_event_content_basic(self):
        """测试基本系统事件内容"""
        content = create_system_event_content(
            event_type="user_joined",
            status="completed"
        )
        
        expected = {
            "system_event_type": "user_joined",
            "status": "completed"
        }
        assert content == expected


class TestMessageInfo:
    """测试MessageInfo Schema"""
    
    def test_message_info_from_text_message(self):
        """测试从文本消息转换MessageInfo"""
        mock_user = MagicMock()
        mock_user.id = "user123"
        mock_user.username = "testuser"
        mock_user.avatar = "/avatars/test.png"

        mock_message = MagicMock()
        mock_message.id = "msg123"
        mock_message.conversation_id = "conv123"
        mock_message.content = {"text": "Hello world"}
        mock_message.type = "text"
        mock_message.sender_id = "user123"
        mock_message.sender_type = "customer"
        mock_message.timestamp = datetime(2025, 1, 25, 10, 0, 0)
        mock_message.is_read = False
        mock_message.is_important = False
        mock_message.reply_to_message_id = None
        mock_message.reactions = {}
        mock_message.extra_metadata = {}
        mock_message.sender = mock_user
        
        message_info = MessageInfo.from_model(mock_message)
        
        assert message_info.id == "msg123"
        assert message_info.content == {"text": "Hello world"}
        assert message_info.type == "text"
        assert message_info.sender.type == "customer"
        assert message_info.sender.name == "testuser" 