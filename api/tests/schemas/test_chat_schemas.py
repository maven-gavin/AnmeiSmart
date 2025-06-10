import pytest
from datetime import datetime
from unittest.mock import MagicMock

from app.schemas.chat import (
    MessageInfo,
    ConversationInfo,
    create_text_message_content,
    create_media_message_content,
    create_system_event_content,
    TextMessageContent,
    MediaMessageContent,
    SystemEventContent,
    MessageCreate
)
from app.db.models.chat import Message, Conversation
from app.db.models.user import User


class TestMessageContentCreators:
    """测试消息内容创建函数"""
    
    def test_create_text_message_content_basic(self):
        """测试基本文本消息内容创建"""
        content = create_text_message_content("Hello world")
        assert content == {"text": "Hello world"}
        assert isinstance(content, dict)
    
    def test_create_text_message_content_empty(self):
        """测试空文本消息内容"""
        content = create_text_message_content("")
        assert content == {"text": ""}
    
    def test_create_text_message_content_unicode(self):
        """测试Unicode文本消息"""
        content = create_text_message_content("你好世界 🌍 emoji test")
        assert content == {"text": "你好世界 🌍 emoji test"}
    
    def test_create_media_message_content_full(self):
        """测试完整媒体消息内容创建"""
        content = create_media_message_content(
            media_url="https://example.com/image.jpg",
            media_name="image.jpg",
            mime_type="image/jpeg",
            size_bytes=123456,
            text="Image description",
            metadata={"width": 800, "height": 600, "camera": "iPhone"}
        )
        
        expected = {
            "text": "Image description",
            "media_info": {
                "url": "https://example.com/image.jpg",
                "name": "image.jpg", 
                "mime_type": "image/jpeg",
                "size_bytes": 123456,
                "metadata": {"width": 800, "height": 600, "camera": "iPhone"}
            }
        }
        assert content == expected
    
    def test_create_media_message_content_minimal(self):
        """测试最小媒体消息内容"""
        content = create_media_message_content(
            media_url="https://example.com/file.pdf",
            media_name="document.pdf",
            mime_type="application/pdf",
            size_bytes=500000
        )

        expected = {
            "text": None,
            "media_info": {
                "url": "https://example.com/file.pdf",
                "name": "document.pdf",
                "mime_type": "application/pdf",
                "size_bytes": 500000,
                "metadata": {}
            }
        }
        assert content == expected
    
    def test_create_media_message_content_with_zero_size(self):
        """测试零大小的媒体文件"""
        content = create_media_message_content(
            media_url="https://example.com/empty.txt",
            media_name="empty.txt",
            mime_type="text/plain",
            size_bytes=0
        )
        
        assert content["media_info"]["size_bytes"] == 0
    
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
    
    def test_create_system_event_content_with_details(self):
        """测试带详情的系统事件"""
        details = {
            "user_id": "user123",
            "username": "john_doe",
            "timestamp": "2025-01-25T10:00:00Z"
        }
        
        content = create_system_event_content(
            event_type="user_joined",
            status="completed",
            details=details
        )
        
        assert content["system_event_type"] == "user_joined"
        assert content["status"] == "completed"
        assert content["details"] == details
    
    def test_create_system_event_content_video_call(self):
        """测试视频通话系统事件"""
        content = create_system_event_content(
            event_type="video_call_status",
            status="ended",
            call_id="vc_123456",
            duration_seconds=300,
            participants=["user1", "user2"]
        )
        
        assert content["system_event_type"] == "video_call_status"
        assert content["call_id"] == "vc_123456"
        assert content["duration_seconds"] == 300
        assert content["participants"] == ["user1", "user2"]


class TestMessageInfo:
    """测试MessageInfo Schema"""
    
    def setup_method(self):
        """设置测试数据"""
        self.mock_user = MagicMock()
        self.mock_user.id = "user123"
        self.mock_user.username = "testuser"
        self.mock_user.avatar = "/avatars/user.png"
        
        self.mock_conversation = MagicMock()
        self.mock_conversation.id = "conv123"
    
    def test_message_info_from_text_message(self):
        """测试从文本消息转换MessageInfo"""
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
        
        # Mock关联对象
        mock_message.sender = self.mock_user
        
        message_info = MessageInfo.from_model(mock_message)
        
        assert message_info.id == "msg123"
        assert message_info.conversation_id == "conv123"
        assert message_info.content == {"text": "Hello world"}
        assert message_info.type == "text"
        assert message_info.sender.type == "customer"
        assert message_info.sender.name == "testuser"
        assert message_info.timestamp == datetime(2025, 1, 25, 10, 0, 0)
        assert message_info.is_read is False
        assert message_info.text_content == "Hello world"
    
    def test_message_info_from_media_message(self):
        """测试从媒体消息转换MessageInfo"""
        media_content = {
            "text": "Check this image",
            "media_info": {
                "url": "https://example.com/image.jpg",
                "name": "photo.jpg",
                "mime_type": "image/jpeg",
                "size_bytes": 123456
            }
        }

        mock_message = MagicMock()
        mock_message.id = "msg456"
        mock_message.conversation_id = "conv123"
        mock_message.content = media_content
        mock_message.type = "media"
        mock_message.sender_id = "user123"
        mock_message.sender_type = "customer"
        mock_message.timestamp = datetime(2025, 1, 25, 10, 0, 0)
        mock_message.is_read = True
        mock_message.is_important = False
        mock_message.reply_to_message_id = None
        mock_message.reactions = {"👍": ["user456"]}
        mock_message.extra_metadata = {"upload_method": "file_picker"}
        mock_message.sender = self.mock_user

        message_info = MessageInfo.from_model(mock_message)

        assert message_info.type == "media"
        assert message_info.text_content == "Check this image"
        assert message_info.media_info.url == "https://example.com/image.jpg"
        assert message_info.media_info.name == "photo.jpg"
        assert message_info.media_info.mime_type == "image/jpeg"
        assert message_info.media_info.size_bytes == 123456
        assert message_info.reactions == {"👍": ["user456"]}
    
    def test_message_info_from_system_message(self):
        """测试从系统消息转换MessageInfo"""
        system_content = {
            "system_event_type": "takeover",
            "status": "completed",
            "details": {"from": "ai", "to": "consultant"}
        }
        
        mock_message = MagicMock()
        mock_message.id = "msg789"
        mock_message.conversation_id = "conv123"
        mock_message.content = system_content
        mock_message.type = "system"
        mock_message.sender_id = "system"
        mock_message.sender_type = "system"
        mock_message.timestamp = datetime(2025, 1, 25, 10, 0, 0)
        mock_message.is_read = True
        mock_message.is_important = False
        mock_message.reply_to_message_id = None
        mock_message.reactions = {}
        mock_message.extra_metadata = {}
        mock_message.sender = None  # 系统消息可能没有sender
        
        message_info = MessageInfo.from_model(mock_message)
        
        assert message_info.type == "system"
        assert message_info.content == system_content
        assert message_info.text_content is None
        assert message_info.media_info is None
    
    def test_message_info_with_reply(self):
        """测试带回复的消息"""
        mock_message = MagicMock()
        mock_message.id = "msg_reply"
        mock_message.conversation_id = "conv123"
        mock_message.content = {"text": "This is a reply"}
        mock_message.type = "text"
        mock_message.sender_id = "user123"
        mock_message.sender_type = "customer"
        mock_message.timestamp = datetime(2025, 1, 25, 10, 0, 0)
        mock_message.is_read = False
        mock_message.is_important = False
        mock_message.reply_to_message_id = "original_msg_123"
        mock_message.reactions = {}
        mock_message.extra_metadata = {}
        mock_message.sender = self.mock_user
        
        message_info = MessageInfo.from_model(mock_message)
        
        assert message_info.reply_to_message_id == "original_msg_123"
    
    def test_message_info_convenience_properties_edge_cases(self):
        """测试便利属性的边界情况"""
        # 测试没有text字段的媒体消息
        mock_message = MagicMock()
        mock_message.content = {
            "media_info": {
                "url": "https://example.com/voice.m4a",
                "name": "voice.m4a",
                "mime_type": "audio/mp4",
                "size_bytes": 1024000  # 添加必需的size_bytes字段
            }
        }
        mock_message.type = "media"
        mock_message.id = "msg_voice"
        mock_message.conversation_id = "conv123"
        mock_message.sender_id = "user123"
        mock_message.sender_type = "customer"
        mock_message.timestamp = datetime.now()
        mock_message.is_read = False
        mock_message.is_important = False
        mock_message.reply_to_message_id = None
        mock_message.reactions = {}
        mock_message.extra_metadata = {}
        mock_message.sender = self.mock_user

        message_info = MessageInfo.from_model(mock_message)

        assert message_info.text_content is None  # 没有text字段
        assert message_info.media_info is not None
        assert message_info.media_info.mime_type == "audio/mp4"


class TestConversationInfo:
    """测试ConversationInfo Schema"""
    
    def test_conversation_info_from_model(self):
        """测试从会话模型转换ConversationInfo"""
        mock_customer = MagicMock()
        mock_customer.id = "customer123"
        mock_customer.username = "customer_user"

        mock_conversation = MagicMock()
        mock_conversation.id = "conv123"
        mock_conversation.title = "Test Conversation"
        mock_conversation.customer_id = "customer123"
        mock_conversation.is_ai_controlled = True
        mock_conversation.created_at = datetime(2025, 1, 25, 9, 0, 0)
        mock_conversation.updated_at = datetime(2025, 1, 25, 10, 0, 0)
        mock_conversation.customer = mock_customer

        conv_info = ConversationInfo.from_model(mock_conversation)

        assert conv_info.id == "conv123"
        assert conv_info.title == "Test Conversation"
        assert conv_info.customer_id == "customer123"
        assert conv_info.is_ai_controlled is True
        # customer 是字典格式，而不是对象
        assert conv_info.customer["id"] == "customer123"
        assert conv_info.customer["username"] == "customer_user"


class TestMessageCreate:
    """测试MessageCreate Schema"""
    
    def test_message_create_text(self):
        """测试创建文本消息"""
        content = create_text_message_content("Test message")
        
        message_create = MessageCreate(
            content=content,
            type="text",
            conversation_id="conv123",
            sender_id="user123",
            sender_type="customer"
        )
        
        assert message_create.content == content
        assert message_create.type == "text"
        assert message_create.conversation_id == "conv123"
        assert message_create.sender_id == "user123"
        assert message_create.sender_type == "customer"
    
    def test_message_create_media(self):
        """测试创建媒体消息"""
        content = create_media_message_content(
            media_url="https://example.com/file.jpg",
            media_name="file.jpg",
            mime_type="image/jpeg",
            size_bytes=123456,
            text="Image caption"
        )
        
        message_create = MessageCreate(
            content=content,
            type="media",
            conversation_id="conv123",
            sender_id="user123",
            sender_type="customer",
            extra_metadata={"upload_method": "drag_drop"}
        )
        
        assert message_create.type == "media"
        assert message_create.extra_metadata == {"upload_method": "drag_drop"}
    
    def test_message_create_with_reply(self):
        """测试创建回复消息"""
        content = create_text_message_content("This is a reply")
        
        message_create = MessageCreate(
            content=content,
            type="text",
            conversation_id="conv123",
            sender_id="user123",
            sender_type="customer",
            reply_to_message_id="original_msg_456"
        )
        
        assert message_create.reply_to_message_id == "original_msg_456"


class TestSchemaValidation:
    """测试Schema验证"""
    
    def test_text_message_content_validation(self):
        """测试文本消息内容验证"""
        # 有效的文本内容
        valid_content = TextMessageContent(text="Valid text")
        assert valid_content.text == "Valid text"
        
        # 测试空文本
        empty_content = TextMessageContent(text="")
        assert empty_content.text == ""
    
    def test_media_message_content_validation(self):
        """测试媒体消息内容验证"""
        media_info = {
            "url": "https://example.com/file.jpg",
            "name": "file.jpg",
            "mime_type": "image/jpeg",
            "size_bytes": 123456
        }

        # 有效的媒体内容
        valid_content = MediaMessageContent(
            media_info=media_info,
            text="Optional text"
        )
        # 比较MediaInfo对象的属性而不是直接比较字典
        assert valid_content.media_info.url == media_info["url"]
        assert valid_content.media_info.name == media_info["name"]
        assert valid_content.media_info.mime_type == media_info["mime_type"]
        assert valid_content.media_info.size_bytes == media_info["size_bytes"]
        assert valid_content.text == "Optional text"
    
    def test_system_event_content_validation(self):
        """测试系统事件内容验证"""
        # 基本系统事件
        basic_event = SystemEventContent(
            system_event_type="user_joined",
            status="completed"
        )
        assert basic_event.system_event_type == "user_joined"
        assert basic_event.status == "completed"
        
        # 带额外字段的系统事件
        complex_event = SystemEventContent(
            system_event_type="video_call",
            status="ended",
            call_id="vc123",
            duration_seconds=300
        )
        assert complex_event.call_id == "vc123"
        assert complex_event.duration_seconds == 300


class TestEdgeCases:
    """测试边界情况"""
    
    def test_very_long_text_content(self):
        """测试很长的文本内容"""
        long_text = "a" * 10000  # 10K characters
        content = create_text_message_content(long_text)
        assert len(content["text"]) == 10000
    
    def test_very_large_media_file(self):
        """测试很大的媒体文件"""
        content = create_media_message_content(
            media_url="https://example.com/large_file.mp4",
            media_name="large_file.mp4",
            mime_type="video/mp4",
            size_bytes=1024 * 1024 * 1024  # 1GB
        )
        assert content["media_info"]["size_bytes"] == 1024 * 1024 * 1024
    
    def test_complex_metadata(self):
        """测试复杂的元数据"""
        complex_metadata = {
            "camera": {
                "make": "Apple",
                "model": "iPhone 15 Pro",
                "settings": {
                    "iso": 400,
                    "aperture": "f/1.8",
                    "shutter_speed": "1/120"
                }
            },
            "location": {
                "latitude": 37.7749,
                "longitude": -122.4194,
                "altitude": 52.5
            },
            "processing": {
                "filters": ["auto_enhance", "color_correction"],
                "ai_enhanced": True
            }
        }
        
        content = create_media_message_content(
            media_url="https://example.com/photo.jpg",
            media_name="photo.jpg",
            mime_type="image/jpeg",
            size_bytes=2048576,
            metadata=complex_metadata
        )
        
        assert content["media_info"]["metadata"] == complex_metadata
    
    def test_unicode_and_emoji_content(self):
        """测试Unicode和emoji内容"""
        unicode_text = "你好世界 🌍 こんにちは 🇯🇵 مرحبا 🌙 Здравствуй 🐻"
        content = create_text_message_content(unicode_text)
        assert content["text"] == unicode_text
        
        # 测试emoji在文件名中
        emoji_filename = "我的照片_😊_2025.jpg"
        content = create_media_message_content(
            media_url="https://example.com/emoji_file.jpg",
            media_name=emoji_filename,
            mime_type="image/jpeg",
            size_bytes=123456
        )
        assert content["media_info"]["name"] == emoji_filename 