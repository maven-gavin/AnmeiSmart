"""
测试消息计数功能
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.chat.domain.entities.conversation import ConversationEntity
from app.chat.domain.entities.message import MessageEntity
from app.chat.domain.conversation_domain_service import ConversationDomainService
from app.chat.application.chat_application_service import ChatApplicationService


class TestMessageCount:
    """测试消息计数功能"""
    
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
    def conversation_domain_service(self, mock_conversation_repository):
        """创建会话领域服务实例"""
        return ConversationDomainService(mock_conversation_repository)
    
    @pytest.fixture
    def sample_conversation(self):
        """创建示例会话"""
        return ConversationEntity(
            id="conv-123",
            title="测试会话",
            ownerId="user-123",
            chatMode="single",
            messageCount=5,
            unreadCount=2
        )
    
    @pytest.fixture
    def sample_message(self):
        """创建示例消息"""
        return MessageEntity(
            id="msg-123",
            conversationId="conv-123",
            content={"text": "测试消息"},
            messageType="text",
            senderId="user-123",
            senderType="customer"
        )
    
    @pytest.mark.asyncio
    async def test_increment_message_count_returns_updated_conversation(
        self, 
        conversation_domain_service, 
        mock_conversation_repository, 
        sample_conversation
    ):
        """测试增加消息数返回更新后的会话实体"""
        # 设置模拟
        mock_conversation_repository.get_by_id.return_value = sample_conversation
        
        # 执行测试
        result = await conversation_domain_service.increment_message_count("conv-123")
        
        # 验证调用
        mock_conversation_repository.get_by_id.assert_called_once_with("conv-123")
        
        # 验证返回更新后的会话
        assert result is not None
        assert result.message_count == 6  # 消息数已增加
        assert result.id == "conv-123"
    
    @pytest.mark.asyncio
    async def test_increment_message_count_conversation_not_found(
        self, 
        conversation_domain_service, 
        mock_conversation_repository
    ):
        """测试会话不存在时的处理"""
        # 设置模拟
        mock_conversation_repository.get_by_id.return_value = None
        
        # 执行测试（不应该抛出异常）
        await conversation_domain_service.increment_message_count("non-existent")
        
        # 验证没有调用保存
        mock_conversation_repository.save.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_conversation_entity_increment_message_count(self, sample_conversation):
        """测试会话实体的消息数增加方法"""
        initial_count = sample_conversation.message_count
        
        # 增加消息数
        sample_conversation.increment_message_count()
        
        # 验证消息数已增加
        assert sample_conversation.message_count == initial_count + 1
        
        # 验证时间戳已更新
        assert sample_conversation.updated_at > sample_conversation.created_at
    
    @pytest.mark.asyncio
    async def test_application_service_saves_updated_conversation(
        self,
        chat_application_service,
        mock_conversation_repository,
        mock_message_repository,
        mock_conversation_domain_service,
        sample_conversation,
        sample_message
    ):
        """测试应用服务负责保存更新后的会话"""
        # 设置模拟
        mock_conversation_repository.get_by_id.return_value = sample_conversation
        mock_message_repository.save.return_value = sample_message
        mock_conversation_domain_service.increment_message_count.return_value = sample_conversation
        mock_conversation_repository.save = AsyncMock()
        
        # 执行测试
        await chat_application_service.send_message_use_case(
            conversation_id="conv-123",
            content="测试消息",
            message_type="text",
            sender_id="user-123",
            sender_type="customer"
        )
        
        # 验证应用服务调用了保存
        mock_conversation_repository.save.assert_called_once_with(sample_conversation)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
