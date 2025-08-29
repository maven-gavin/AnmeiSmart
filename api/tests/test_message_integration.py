"""
测试消息发送集成功能
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.chat.domain.entities.conversation import Conversation
from app.services.chat.domain.entities.message import Message
from app.services.chat.application.chat_application_service import ChatApplicationService


class TestMessageIntegration:
    """测试消息发送集成功能"""
    
    @pytest.fixture
    def mock_conversation_repository(self):
        """模拟会话仓储"""
        mock_repo = AsyncMock()
        return mock_repo
    
    @pytest.fixture
    def mock_message_repository(self):
        """模拟消息仓储"""
        mock_repo = AsyncMock()
        return mock_repo
    
    @pytest.fixture
    def mock_conversation_domain_service(self):
        """模拟会话领域服务"""
        mock_service = AsyncMock()
        return mock_service
    
    @pytest.fixture
    def mock_message_domain_service(self):
        """模拟消息领域服务"""
        mock_service = AsyncMock()
        return mock_service
    
    @pytest.fixture
    def mock_broadcasting_service(self):
        """模拟广播服务"""
        mock_service = AsyncMock()
        return mock_service
    
    @pytest.fixture
    def chat_application_service(
        self,
        mock_conversation_repository,
        mock_message_repository,
        mock_conversation_domain_service,
        mock_message_domain_service,
        mock_broadcasting_service
    ):
        """创建聊天应用服务实例"""
        service = ChatApplicationService(
            conversation_repository=mock_conversation_repository,
            message_repository=mock_message_repository,
            conversation_domain_service=mock_conversation_domain_service,
            message_domain_service=mock_message_domain_service,
            broadcasting_service=mock_broadcasting_service
        )
        return service
    
    @pytest.fixture
    def sample_conversation(self):
        """创建示例会话"""
        return Conversation(
            id="conv-123",
            title="测试会话",
            owner_id="user-123",
            conversation_type="single",
            message_count=5,
            unread_count=2
        )
    
    @pytest.fixture
    def sample_message(self):
        """创建示例消息"""
        return Message(
            id="msg-123",
            conversation_id="conv-123",
            content={"text": "测试消息"},
            message_type="text",
            sender_id="user-123",
            sender_type="customer"
        )
    
    @pytest.fixture
    def mock_user(self):
        """模拟用户"""
        user = MagicMock()
        user.id = "user-123"
        user.roles = [MagicMock(name="customer")]
        return user
    
    @pytest.mark.asyncio
    async def test_send_message_updates_conversation_count(
        self,
        chat_application_service,
        mock_conversation_repository,
        mock_message_repository,
        mock_conversation_domain_service,
        sample_conversation,
        sample_message,
        mock_user
    ):
        """测试发送消息时会更新会话消息数"""
        # 设置模拟
        mock_conversation_repository.get_by_id.return_value = sample_conversation
        mock_message_repository.save.return_value = sample_message
        mock_conversation_domain_service.increment_message_count = AsyncMock()
        
        # 执行测试
        await chat_application_service.send_message_use_case(
            conversation_id="conv-123",
            content="测试消息",
            message_type="text",
            sender_id="user-123",
            sender_type="customer"
        )
        
        # 验证消息保存
        mock_message_repository.save.assert_called_once()
        
        # 验证消息数更新
        mock_conversation_domain_service.increment_message_count.assert_called_once_with("conv-123")
    
    @pytest.mark.asyncio
    async def test_send_message_with_dict_content(
        self,
        chat_application_service,
        mock_conversation_repository,
        mock_message_repository,
        mock_conversation_domain_service,
        sample_conversation,
        sample_message,
        mock_user
    ):
        """测试发送字典格式内容的消息"""
        # 设置模拟
        mock_conversation_repository.get_by_id.return_value = sample_conversation
        mock_message_repository.save.return_value = sample_message
        mock_conversation_domain_service.increment_message_count = AsyncMock()
        
        # 执行测试
        content = {"text": "测试消息", "media_url": "http://example.com/image.jpg"}
        await chat_application_service.send_message_use_case(
            conversation_id="conv-123",
            content=content,
            message_type="media",
            sender_id="user-123",
            sender_type="customer"
        )
        
        # 验证消息保存时使用了正确的content
        saved_message = mock_message_repository.save.call_args[0][0]
        assert saved_message.content == content
        assert saved_message.message_type == "media"
    
    @pytest.mark.asyncio
    async def test_send_message_conversation_not_found(
        self,
        chat_application_service,
        mock_conversation_repository
    ):
        """测试会话不存在时的错误处理"""
        # 设置模拟
        mock_conversation_repository.get_by_id.return_value = None
        
        # 执行测试并验证异常
        with pytest.raises(ValueError, match="会话不存在"):
            await chat_application_service.send_message_use_case(
                conversation_id="non-existent",
                content="测试消息",
                message_type="text",
                sender_id="user-123",
                sender_type="user"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
