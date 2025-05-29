import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.chat.ai_response_service import AIResponseService
import types

@pytest.mark.asyncio
async def test_generate_ai_response_success():
    service = AIResponseService(db=MagicMock())
    service.get_conversation_history = MagicMock(return_value=[{"content": "hi", "sender_type": "customer", "timestamp": "2024-01-01T00:00:00"}])
    service.ai_service = MagicMock()
    service.ai_service.get_response = AsyncMock(return_value={"content": "AI回复"})
    service.message_service = MagicMock()
    service.message_service.create_message = AsyncMock(return_value=types.SimpleNamespace(id="msg1", content="AI回复"))
    with patch("app.core.events.create_message_event") as mock_event, \
         patch("app.core.events.event_bus.publish_async", new_callable=AsyncMock):
        await service.generate_ai_response("conv1", "你好")
        service.get_conversation_history.assert_called_once_with("conv1")
        service.ai_service.get_response.assert_awaited_once()
        service.message_service.create_message.assert_awaited_once()
        mock_event.assert_called_once()

@pytest.mark.asyncio
async def test_generate_ai_response_timeout():
    service = AIResponseService(db=MagicMock())
    service.get_conversation_history = MagicMock(return_value=[{"content": "hi", "sender_type": "customer", "timestamp": "2024-01-01T00:00:00"}])
    service.ai_service = MagicMock()
    service.ai_service.get_response = AsyncMock(side_effect=asyncio.TimeoutError)
    service.create_timeout_message = AsyncMock()
    with patch("app.services.chat.ai_response_service.logger"):
        await service.generate_ai_response("conv1", "你好")
        service.create_timeout_message.assert_awaited_once_with("conv1")

@pytest.mark.asyncio
async def test_generate_ai_response_exception():
    service = AIResponseService(db=MagicMock())
    service.get_conversation_history = MagicMock(return_value=[{"content": "hi", "sender_type": "customer", "timestamp": "2024-01-01T00:00:00"}])
    service.ai_service = MagicMock()
    service.ai_service.get_response = AsyncMock(side_effect=Exception("error"))
    service.create_error_message = AsyncMock()
    with patch("app.services.chat.ai_response_service.logger"):
        await service.generate_ai_response("conv1", "你好")
        service.create_error_message.assert_awaited_once()

@pytest.mark.asyncio
async def test_generate_ai_response_ai_response_type_error():
    service = AIResponseService(db=MagicMock())
    service.get_conversation_history = MagicMock(return_value=[{"content": "hi", "sender_type": "customer", "timestamp": "2024-01-01T00:00:00"}])
    service.ai_service = MagicMock()
    service.ai_service.get_response = AsyncMock(return_value="not a dict")
    service.create_error_message = AsyncMock()
    with patch("app.services.chat.ai_response_service.logger"):
        await service.generate_ai_response("conv1", "你好")
        service.create_error_message.assert_awaited_once_with("conv1", "AI服务返回格式错误") 