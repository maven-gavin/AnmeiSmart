import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.chat.ai_response_service import AIResponseService
import types

@pytest.mark.asyncio
async def test_generate_ai_response_success():
    service = AIResponseService(db=MagicMock())
    service.get_conversation_history = MagicMock(return_value=[{"content": "hi", "sender_type": "customer", "timestamp": "2024-01-01T00:00:00"}])
    service.message_service = MagicMock()
    service.message_service.create_message = AsyncMock(return_value=types.SimpleNamespace(id="msg1", content="AI回复"))
    
    # 模拟AI服务
    mock_ai_service = MagicMock()
    mock_ai_service.get_response = AsyncMock(return_value={"content": "AI回复"})
    
    with patch("app.core.events.create_message_event") as mock_event, \
         patch("app.core.events.event_bus.publish_async", new_callable=AsyncMock), \
         patch("app.services.ai.get_ai_service", return_value=mock_ai_service) as mock_get_ai_service:
        await service.generate_ai_response("conv1", "你好")
        service.get_conversation_history.assert_called_once_with("conv1")
        mock_get_ai_service.assert_called_once_with(service.db)
        mock_ai_service.get_response.assert_awaited_once()
        service.message_service.create_message.assert_awaited_once()
        mock_event.assert_called_once()

@pytest.mark.asyncio
async def test_generate_ai_response_timeout():
    service = AIResponseService(db=MagicMock())
    service.get_conversation_history = MagicMock(return_value=[{"content": "hi", "sender_type": "customer", "timestamp": "2024-01-01T00:00:00"}])
    service.create_timeout_message = AsyncMock()
    
    # 模拟AI服务超时
    mock_ai_service = MagicMock()
    mock_ai_service.get_response = AsyncMock(side_effect=asyncio.TimeoutError)
    
    with patch("app.services.chat.ai_response_service.logger"), \
         patch("app.services.ai.get_ai_service", return_value=mock_ai_service):
        await service.generate_ai_response("conv1", "你好")
        service.create_timeout_message.assert_awaited_once_with("conv1")

@pytest.mark.asyncio
async def test_generate_ai_response_exception():
    service = AIResponseService(db=MagicMock())
    service.get_conversation_history = MagicMock(return_value=[{"content": "hi", "sender_type": "customer", "timestamp": "2024-01-01T00:00:00"}])
    service.create_error_message = AsyncMock()
    
    # 模拟AI服务异常
    mock_ai_service = MagicMock()
    mock_ai_service.get_response = AsyncMock(side_effect=Exception("error"))
    
    with patch("app.services.chat.ai_response_service.logger"), \
         patch("app.services.ai.get_ai_service", return_value=mock_ai_service):
        await service.generate_ai_response("conv1", "你好")
        service.create_error_message.assert_awaited_once()

@pytest.mark.asyncio
async def test_generate_ai_response_ai_response_type_error():
    service = AIResponseService(db=MagicMock())
    service.get_conversation_history = MagicMock(return_value=[{"content": "hi", "sender_type": "customer", "timestamp": "2024-01-01T00:00:00"}])
    service.create_error_message = AsyncMock()
    
    # 模拟AI服务返回类型错误
    mock_ai_service = MagicMock()
    mock_ai_service.get_response = AsyncMock(return_value="not a dict")
    
    with patch("app.services.chat.ai_response_service.logger"), \
         patch("app.services.ai.get_ai_service", return_value=mock_ai_service):
        await service.generate_ai_response("conv1", "你好")
        service.create_error_message.assert_awaited_once_with("conv1", "AI服务返回格式错误") 