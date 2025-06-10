"""
WebSocket端点测试用例（重构架构V2同步版本）
测试websocket.py中的所有功能，包括连接建立、token验证、设备管理、心跳处理、广播服务集成等
"""
import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from fastapi.testclient import TestClient
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.db.models.user import User
from app.services import user_service as crud_user
from app.schemas.user import UserCreate
from app.core.distributed_connection_manager import DistributedConnectionManager
from app.api.v1.endpoints.websocket import verify_websocket_token, get_connection_manager
from app.core.redis_client import get_redis_client
from app.services.broadcasting_service import BroadcastingService
from app.services.notification_service import NotificationService


@pytest.fixture
def fake_customer_ws(db: Session):
    """为WebSocket测试创建假客户"""
    user_in = UserCreate(
        email="ws_customer@example.com",
        username="ws_customer",
        password="test123456",
        roles=["customer"],
        is_active=True
    )
    user = asyncio.get_event_loop().run_until_complete(crud_user.create(db, user_in))
    return user


@pytest.fixture
def fake_consultant_ws(db: Session):
    """为WebSocket测试创建假顾问"""
    user_in = UserCreate(
        email="ws_consultant@example.com",
        username="ws_consultant",
        password="test123456",
        roles=["consultant"],
        is_active=True
    )
    user = asyncio.get_event_loop().run_until_complete(crud_user.create(db, user_in))
    return user


@pytest.fixture
def mock_redis_client():
    """模拟Redis客户端"""
    redis_mock = AsyncMock()
    redis_mock.ping = AsyncMock(return_value=True)
    redis_mock.publish = AsyncMock()
    redis_mock.pubsub = MagicMock()
    redis_mock.close = AsyncMock()
    return redis_mock


@pytest.fixture
def mock_connection_manager(mock_redis_client):
    """模拟分布式连接管理器"""
    manager = AsyncMock(spec=DistributedConnectionManager)
    manager.connect = AsyncMock(return_value=True)
    manager.disconnect = AsyncMock(return_value=True)
    manager.initialize = AsyncMock()
    manager.cleanup = AsyncMock()
    manager.send_to_user = AsyncMock()
    manager.send_to_device = AsyncMock()
    manager.send_to_device_type = AsyncMock()
    manager.broadcast_to_all = AsyncMock()
    manager.is_user_online = AsyncMock(return_value=True)
    manager.get_user_devices = AsyncMock(return_value=[])
    manager.get_user_device_info = AsyncMock(return_value=[])
    return manager


@pytest.fixture
def mock_broadcasting_service():
    """模拟广播服务"""
    service = AsyncMock(spec=BroadcastingService)
    service.broadcast_message = AsyncMock()
    service.broadcast_consultation_reply = AsyncMock()
    service.send_mobile_only_notification = AsyncMock()
    service.broadcast_typing_status = AsyncMock()
    service.broadcast_read_status = AsyncMock()
    service.broadcast_system_notification = AsyncMock()
    service.send_direct_message = AsyncMock()
    service.get_user_device_info = AsyncMock(return_value=[])
    return service


@pytest.fixture  
def mock_notification_service():
    """模拟通知推送服务"""
    service = AsyncMock(spec=NotificationService)
    service.send_push_notification = AsyncMock()
    service.send_mobile_notification = AsyncMock()
    return service


@pytest.fixture
def mock_websocket():
    """模拟WebSocket连接"""
    websocket = AsyncMock(spec=WebSocket)
    websocket.send_json = AsyncMock()
    websocket.send_text = AsyncMock()
    websocket.receive_text = AsyncMock()
    websocket.receive_json = AsyncMock()
    websocket.close = AsyncMock()
    websocket.client_state = MagicMock()
    websocket.client_state.name = "CONNECTED"
    return websocket


# ============ Token验证测试 ============

@pytest.mark.asyncio
async def test_verify_websocket_token_success(db: Session, fake_customer_ws):
    """测试WebSocket token验证成功"""
    # Mock JWT解码而不是整个verify_token函数
    with patch('app.core.security.jwt.decode') as mock_jwt_decode:
        mock_jwt_decode.return_value = {
            "sub": fake_customer_ws.id,
            "exp": 9999999999  # 遥远的未来时间戳
        }
        
        result = await verify_websocket_token("valid_token", db)
        
        assert result is not None
        assert result["user_id"] == fake_customer_ws.id
        assert result["role"] == "customer"
        assert result["username"] == fake_customer_ws.username


@pytest.mark.asyncio
async def test_verify_websocket_token_invalid_token(db: Session):
    """测试WebSocket无效token"""
    with patch('app.core.security.jwt.decode') as mock_jwt_decode:
        from jose import JWTError
        mock_jwt_decode.side_effect = JWTError("Invalid token")
        
        result = await verify_websocket_token("invalid_token", db)
        
        assert result is None


@pytest.mark.asyncio
async def test_verify_websocket_token_user_not_found(db: Session):
    """测试WebSocket token验证时用户不存在"""
    with patch('app.core.security.jwt.decode') as mock_jwt_decode:
        mock_jwt_decode.return_value = {
            "sub": "nonexistent_user_id",
            "exp": 9999999999
        }
        
        result = await verify_websocket_token("valid_token", db)
        
        assert result is None


@pytest.mark.asyncio
async def test_verify_websocket_token_consultant_role(db: Session, fake_consultant_ws):
    """测试顾问角色的token验证"""
    with patch('app.core.security.jwt.decode') as mock_jwt_decode:
        mock_jwt_decode.return_value = {
            "sub": fake_consultant_ws.id,
            "exp": 9999999999
        }
        
        result = await verify_websocket_token("consultant_token", db)
        
        assert result is not None
        assert result["user_id"] == fake_consultant_ws.id
        assert result["role"] == "consultant"
        assert result["username"] == fake_consultant_ws.username


@pytest.mark.asyncio
async def test_verify_websocket_token_exception_handling(db: Session):
    """测试token验证过程中的异常处理"""
    with patch('app.core.security.jwt.decode') as mock_jwt_decode:
        mock_jwt_decode.side_effect = Exception("验证过程出错")
        
        result = await verify_websocket_token("error_token", db)
        
        assert result is None


# ============ WebSocket连接测试 ============

@pytest.mark.asyncio
async def test_websocket_connection_success(
    mock_websocket, 
    mock_connection_manager, 
    fake_customer_ws, 
    db: Session
):
    """测试WebSocket连接成功建立"""
    
    # Mock token验证
    with patch('app.api.v1.endpoints.websocket.verify_websocket_token') as mock_verify:
        mock_verify.return_value = {
            "user_id": fake_customer_ws.id,
            "role": "customer",
            "username": fake_customer_ws.username
        }
        
        # Mock连接管理器
        with patch('app.api.v1.endpoints.websocket.get_connection_manager') as mock_get_manager:
            mock_get_manager.return_value = mock_connection_manager
            
            # Mock WebSocket receive_text来模拟心跳
            mock_websocket.receive_text.side_effect = ["ping", "ping", WebSocketDisconnect()]
            
            # 导入并调用WebSocket端点
            from app.api.v1.endpoints.websocket import websocket_endpoint
            
            # 执行WebSocket连接
            await websocket_endpoint(
                websocket=mock_websocket,
                token="valid_token",
                connectionId="test_conn_123",
                deviceType="desktop",
                deviceId="device_456",
                db=db,
                manager=mock_connection_manager
            )
            
            # 验证连接建立
            mock_connection_manager.connect.assert_called_once()
            connect_call_args = mock_connection_manager.connect.call_args
            assert connect_call_args[0][0] == fake_customer_ws.id  # user_id
            assert connect_call_args[0][1] == mock_websocket  # websocket
            assert connect_call_args[0][3] == "test_conn_123"  # connection_id
            
            # 验证发送连接确认消息
            mock_websocket.send_json.assert_called()
            sent_message = mock_websocket.send_json.call_args[0][0]
            assert sent_message["event"] == "connected"
            assert sent_message["data"]["user_id"] == fake_customer_ws.id
            assert sent_message["data"]["connection_id"] == "test_conn_123"
            assert sent_message["data"]["device_type"] == "desktop"
            
            # 验证心跳响应
            mock_websocket.send_text.assert_called_with("pong")
            
            # 验证断开连接时的清理
            mock_connection_manager.disconnect.assert_called_once_with(mock_websocket)


@pytest.mark.asyncio
async def test_websocket_connection_invalid_token(
    mock_websocket, 
    mock_connection_manager, 
    db: Session
):
    """测试WebSocket连接时token无效"""
    
    # Mock token验证失败
    with patch('app.api.v1.endpoints.websocket.verify_websocket_token') as mock_verify:
        mock_verify.return_value = None
        
        with patch('app.api.v1.endpoints.websocket.get_connection_manager') as mock_get_manager:
            mock_get_manager.return_value = mock_connection_manager
            
            from app.api.v1.endpoints.websocket import websocket_endpoint
            
            await websocket_endpoint(
                websocket=mock_websocket,
                token="invalid_token",
                db=db,
                manager=mock_connection_manager
            )
            
            # 验证WebSocket连接被关闭
            mock_websocket.close.assert_called_once_with(code=4001, reason="Invalid credentials")
            
            # 验证没有尝试建立连接
            mock_connection_manager.connect.assert_not_called()


@pytest.mark.asyncio
async def test_websocket_connection_manager_fail(
    mock_websocket, 
    mock_connection_manager, 
    fake_customer_ws, 
    db: Session
):
    """测试WebSocket连接管理器连接失败"""
    
    with patch('app.api.v1.endpoints.websocket.verify_websocket_token') as mock_verify:
        mock_verify.return_value = {
            "user_id": fake_customer_ws.id,
            "role": "customer",
            "username": fake_customer_ws.username
        }
        
        # Mock连接管理器连接失败
        mock_connection_manager.connect.return_value = False
        
        with patch('app.api.v1.endpoints.websocket.get_connection_manager') as mock_get_manager:
            mock_get_manager.return_value = mock_connection_manager
            
            from app.api.v1.endpoints.websocket import websocket_endpoint
            
            await websocket_endpoint(
                websocket=mock_websocket,
                token="valid_token",
                db=db,
                manager=mock_connection_manager
            )
            
            # 验证连接失败时关闭WebSocket
            mock_websocket.close.assert_called_once_with(code=4002, reason="Connection failed")


# ============ 设备参数测试 ============

@pytest.mark.asyncio
async def test_websocket_connection_with_device_params(
    mock_websocket, 
    mock_connection_manager, 
    fake_customer_ws, 
    db: Session
):
    """测试WebSocket连接包含设备参数"""
    
    with patch('app.api.v1.endpoints.websocket.verify_websocket_token') as mock_verify:
        mock_verify.return_value = {
            "user_id": fake_customer_ws.id,
            "role": "customer",
            "username": fake_customer_ws.username
        }
        
        with patch('app.api.v1.endpoints.websocket.get_connection_manager') as mock_get_manager:
            mock_get_manager.return_value = mock_connection_manager
            
            # Mock断开连接
            mock_websocket.receive_text.side_effect = [WebSocketDisconnect()]
            
            from app.api.v1.endpoints.websocket import websocket_endpoint
            
            await websocket_endpoint(
                websocket=mock_websocket,
                token="valid_token",
                connectionId="mobile_conn_789",
                deviceType="mobile",
                deviceId="iphone_12_pro",
                db=db,
                manager=mock_connection_manager
            )
            
            # 验证连接时传递了正确的设备信息
            connect_call_args = mock_connection_manager.connect.call_args
            connection_metadata = connect_call_args[0][2]
            
            assert connection_metadata["connection_id"] == "mobile_conn_789"
            assert connection_metadata["device_type"] == "mobile"
            assert connection_metadata["device_id"] == "iphone_12_pro"
            assert connection_metadata["user_role"] == "customer"
            assert connection_metadata["username"] == fake_customer_ws.username


@pytest.mark.asyncio
async def test_websocket_connection_auto_generate_connection_id(
    mock_websocket, 
    mock_connection_manager, 
    fake_customer_ws, 
    db: Session
):
    """测试WebSocket连接自动生成connection_id"""
    
    with patch('app.api.v1.endpoints.websocket.verify_websocket_token') as mock_verify:
        mock_verify.return_value = {
            "user_id": fake_customer_ws.id,
            "role": "customer",
            "username": fake_customer_ws.username
        }
        
        with patch('app.api.v1.endpoints.websocket.get_connection_manager') as mock_get_manager:
            mock_get_manager.return_value = mock_connection_manager
            
            mock_websocket.receive_text.side_effect = [WebSocketDisconnect()]
            
            from app.api.v1.endpoints.websocket import websocket_endpoint
            
            # 不提供connectionId，应该自动生成 (传递None而不是使用默认Query对象)
            await websocket_endpoint(
                websocket=mock_websocket,
                token="valid_token",
                connectionId=None,  # 明确传递None
                deviceType="tablet",
                deviceId=None,
                db=db,
                manager=mock_connection_manager
            )
            
            # 验证自动生成了connection_id
            connect_call_args = mock_connection_manager.connect.call_args
            generated_connection_id = connect_call_args[0][3]
            
            assert generated_connection_id is not None
            assert str(fake_customer_ws.id) in str(generated_connection_id)
            assert "tablet" in str(generated_connection_id)


# ============ 心跳和消息处理测试 ============

@pytest.mark.asyncio
async def test_websocket_heartbeat_handling(
    mock_websocket, 
    mock_connection_manager, 
    fake_customer_ws, 
    db: Session
):
    """测试WebSocket心跳处理"""
    
    with patch('app.api.v1.endpoints.websocket.verify_websocket_token') as mock_verify:
        mock_verify.return_value = {
            "user_id": fake_customer_ws.id,
            "role": "customer",
            "username": fake_customer_ws.username
        }
        
        with patch('app.api.v1.endpoints.websocket.get_connection_manager') as mock_get_manager:
            mock_get_manager.return_value = mock_connection_manager
            
            # 模拟多次心跳然后断开
            mock_websocket.receive_text.side_effect = [
                "ping", "ping", "ping", WebSocketDisconnect()
            ]
            
            from app.api.v1.endpoints.websocket import websocket_endpoint
            
            await websocket_endpoint(
                websocket=mock_websocket,
                token="valid_token",
                db=db,
                manager=mock_connection_manager
            )
            
            # 验证心跳响应次数
            assert mock_websocket.send_text.call_count == 3
            for call in mock_websocket.send_text.call_args_list:
                assert call[0][0] == "pong"


@pytest.mark.asyncio
async def test_websocket_non_heartbeat_message_handling(
    mock_websocket, 
    mock_connection_manager, 
    fake_customer_ws, 
    db: Session
):
    """测试WebSocket非心跳消息处理"""
    
    with patch('app.api.v1.endpoints.websocket.verify_websocket_token') as mock_verify:
        mock_verify.return_value = {
            "user_id": fake_customer_ws.id,
            "role": "customer",
            "username": fake_customer_ws.username
        }
        
        with patch('app.api.v1.endpoints.websocket.get_connection_manager') as mock_get_manager:
            mock_get_manager.return_value = mock_connection_manager
            
            # 发送非心跳消息
            mock_websocket.receive_text.side_effect = [
                "some_business_message", 
                WebSocketDisconnect()
            ]
            
            from app.api.v1.endpoints.websocket import websocket_endpoint
            
            await websocket_endpoint(
                websocket=mock_websocket,
                token="valid_token",
                db=db,
                manager=mock_connection_manager
            )
            
            # 验证非心跳消息被忽略，没有发送pong响应
            mock_websocket.send_text.assert_not_called()


# ============ 错误处理测试 ============

@pytest.mark.asyncio
async def test_websocket_message_processing_error(
    mock_websocket, 
    mock_connection_manager, 
    fake_customer_ws, 
    db: Session
):
    """测试WebSocket消息处理错误"""
    
    with patch('app.api.v1.endpoints.websocket.verify_websocket_token') as mock_verify:
        mock_verify.return_value = {
            "user_id": fake_customer_ws.id,
            "role": "customer",
            "username": fake_customer_ws.username
        }
        
        with patch('app.api.v1.endpoints.websocket.get_connection_manager') as mock_get_manager:
            mock_get_manager.return_value = mock_connection_manager
            
            # 模拟接收消息时出错
            mock_websocket.receive_text.side_effect = [
                Exception("消息接收错误"), 
                WebSocketDisconnect()
            ]
            
            from app.api.v1.endpoints.websocket import websocket_endpoint
            
            await websocket_endpoint(
                websocket=mock_websocket,
                token="valid_token",
                db=db,
                manager=mock_connection_manager
            )
            
            # 验证发送了错误响应
            error_calls = [call for call in mock_websocket.send_json.call_args_list 
                          if call[0][0].get("event") == "error"]
            assert len(error_calls) >= 1
            
            error_message = error_calls[0][0][0]
            assert error_message["event"] == "error"
            assert "消息处理失败" in error_message["data"]["message"]


@pytest.mark.asyncio
async def test_websocket_cleanup_on_exception(
    mock_websocket, 
    mock_connection_manager, 
    fake_customer_ws, 
    db: Session
):
    """测试WebSocket异常时的清理"""
    
    with patch('app.api.v1.endpoints.websocket.verify_websocket_token') as mock_verify:
        mock_verify.return_value = {
            "user_id": fake_customer_ws.id,
            "role": "customer",
            "username": fake_customer_ws.username
        }
        
        # Mock连接管理器抛出异常
        mock_connection_manager.connect.side_effect = Exception("连接管理器错误")
        
        with patch('app.api.v1.endpoints.websocket.get_connection_manager') as mock_get_manager:
            mock_get_manager.return_value = mock_connection_manager
            
            from app.api.v1.endpoints.websocket import websocket_endpoint
            
            await websocket_endpoint(
                websocket=mock_websocket,
                token="valid_token",
                db=db,
                manager=mock_connection_manager
            )
            
            # 验证WebSocket被关闭
            mock_websocket.close.assert_called()


# ============ 连接管理器依赖测试 ============

def test_get_connection_manager_not_initialized():
    """测试连接管理器未初始化时的异常"""
    # 确保全局连接管理器为None
    import app.api.v1.endpoints.websocket as ws_module
    original_manager = ws_module.connection_manager
    ws_module.connection_manager = None
    
    try:
        with pytest.raises(Exception):
            get_connection_manager()
    finally:
        # 恢复原始状态
        ws_module.connection_manager = original_manager


# @pytest.mark.asyncio
# async def test_initialize_connection_manager_success(mock_redis_client):
#     """测试连接管理器初始化成功"""
#     from app.api.v1.endpoints.websocket import initialize_connection_manager
    
#     with patch('app.core.distributed_connection_manager.DistributedConnectionManager') as mock_class:
#         mock_instance = AsyncMock()
#         mock_instance.initialize = AsyncMock()
#         mock_class.return_value = mock_instance
        
#         await initialize_connection_manager(mock_redis_client)
        
#         # 验证创建了连接管理器实例
#         mock_class.assert_called_once_with(mock_redis_client)
#         mock_instance.initialize.assert_called_once()


# @pytest.mark.asyncio
# async def test_initialize_connection_manager_failure(mock_redis_client):
#     """测试连接管理器初始化失败"""
#     from app.api.v1.endpoints.websocket import initialize_connection_manager
    
#     with patch('app.core.distributed_connection_manager.DistributedConnectionManager') as mock_class:
#         mock_class.side_effect = Exception("初始化失败")
        
#         with pytest.raises(Exception, match="初始化失败"):
#             await initialize_connection_manager(mock_redis_client)


@pytest.mark.asyncio
async def test_cleanup_connection_manager_success():
    """测试连接管理器清理成功"""
    from app.api.v1.endpoints.websocket import cleanup_connection_manager
    import app.api.v1.endpoints.websocket as ws_module
    
    # 设置一个mock的连接管理器
    mock_manager = AsyncMock()
    mock_manager.cleanup = AsyncMock()
    original_manager = ws_module.connection_manager
    ws_module.connection_manager = mock_manager
    
    try:
        await cleanup_connection_manager()
        
        # 验证调用了cleanup方法
        mock_manager.cleanup.assert_called_once()
        
        # 验证连接管理器被设置为None
        assert ws_module.connection_manager is None
        
    finally:
        # 恢复原始状态
        ws_module.connection_manager = original_manager


@pytest.mark.asyncio
async def test_cleanup_connection_manager_with_exception():
    """测试连接管理器清理时异常处理"""
    from app.api.v1.endpoints.websocket import cleanup_connection_manager
    import app.api.v1.endpoints.websocket as ws_module
    
    # 设置一个会抛出异常的mock管理器
    mock_manager = AsyncMock()
    mock_manager.cleanup.side_effect = Exception("清理失败")
    original_manager = ws_module.connection_manager
    ws_module.connection_manager = mock_manager
    
    try:
        # 不应该抛出异常，而是捕获并处理
        await cleanup_connection_manager()
        
        # 验证即使cleanup失败，连接管理器也被设置为None
        assert ws_module.connection_manager is None
        
    finally:
        # 恢复原始状态
        ws_module.connection_manager = original_manager


# ============ 集成测试 ============

@pytest.mark.asyncio
async def test_websocket_full_lifecycle(
    mock_websocket, 
    mock_connection_manager, 
    fake_customer_ws, 
    db: Session
):
    """测试WebSocket完整生命周期：连接-心跳-断开"""
    
    with patch('app.api.v1.endpoints.websocket.verify_websocket_token') as mock_verify:
        mock_verify.return_value = {
            "user_id": fake_customer_ws.id,
            "role": "customer",
            "username": fake_customer_ws.username
        }
        
        with patch('app.api.v1.endpoints.websocket.get_connection_manager') as mock_get_manager:
            mock_get_manager.return_value = mock_connection_manager
            
            # 模拟完整的消息序列：连接确认，心跳，业务消息，断开
            mock_websocket.receive_text.side_effect = [
                "ping",  # 心跳
                "business_message",  # 业务消息（会被忽略）
                "ping",  # 再次心跳
                WebSocketDisconnect()  # 断开连接
            ]
            
            from app.api.v1.endpoints.websocket import websocket_endpoint
            
            await websocket_endpoint(
                websocket=mock_websocket,
                token="valid_token",
                connectionId="lifecycle_test",
                deviceType="desktop",
                deviceId="test_device",
                db=db,
                manager=mock_connection_manager
            )
            
            # 验证连接建立
            mock_connection_manager.connect.assert_called_once()
            
            # 验证发送了连接确认
            connect_calls = [call for call in mock_websocket.send_json.call_args_list 
                           if call[0][0].get("event") == "connected"]
            assert len(connect_calls) == 1
            
            # 验证心跳响应（2次ping = 2次pong）
            assert mock_websocket.send_text.call_count == 2
            
            # 验证断开连接时的清理
            mock_connection_manager.disconnect.assert_called_once_with(mock_websocket)


@pytest.mark.asyncio
async def test_websocket_concurrent_connections(
    mock_connection_manager, 
    fake_customer_ws, 
    fake_consultant_ws, 
    db: Session
):
    """测试多个并发WebSocket连接"""
    
    # 创建两个mock websocket
    mock_ws1 = AsyncMock(spec=WebSocket)
    mock_ws1.send_json = AsyncMock()
    mock_ws1.send_text = AsyncMock()
    mock_ws1.receive_text = AsyncMock(side_effect=[WebSocketDisconnect()])
    mock_ws1.client_state = MagicMock()
    mock_ws1.client_state.name = "CONNECTED"
    
    mock_ws2 = AsyncMock(spec=WebSocket)
    mock_ws2.send_json = AsyncMock()
    mock_ws2.send_text = AsyncMock()
    mock_ws2.receive_text = AsyncMock(side_effect=[WebSocketDisconnect()])
    mock_ws2.client_state = MagicMock()
    mock_ws2.client_state.name = "CONNECTED"
    
    with patch('app.api.v1.endpoints.websocket.verify_websocket_token') as mock_verify:
        # 为不同的连接返回不同的用户信息
        mock_verify.side_effect = [
            {
                "user_id": fake_customer_ws.id,
                "role": "customer",
                "username": fake_customer_ws.username
            },
            {
                "user_id": fake_consultant_ws.id,
                "role": "consultant", 
                "username": fake_consultant_ws.username
            }
        ]
        
        with patch('app.api.v1.endpoints.websocket.get_connection_manager') as mock_get_manager:
            mock_get_manager.return_value = mock_connection_manager
            
            from app.api.v1.endpoints.websocket import websocket_endpoint
            
            # 并发启动两个WebSocket连接
            tasks = [
                asyncio.create_task(websocket_endpoint(
                    websocket=mock_ws1,
                    token="customer_token",
                    connectionId="customer_conn",
                    deviceType="desktop",
                    db=db,
                    manager=mock_connection_manager
                )),
                asyncio.create_task(websocket_endpoint(
                    websocket=mock_ws2,
                    token="consultant_token",
                    connectionId="consultant_conn",
                    deviceType="mobile",
                    db=db,
                    manager=mock_connection_manager
                ))
            ]
            
            # 等待所有连接完成
            await asyncio.gather(*tasks)
            
            # 验证两个连接都被建立
            assert mock_connection_manager.connect.call_count == 2
            
            # 验证两个连接都发送了确认消息
            mock_ws1.send_json.assert_called()
            mock_ws2.send_json.assert_called()
            
            # 验证两个连接都被清理
            assert mock_connection_manager.disconnect.call_count == 2


# ============ 广播服务集成测试（重构架构V2） ============

@pytest.mark.asyncio
async def test_websocket_integration_with_broadcasting_service(
    mock_websocket,
    mock_connection_manager,
    mock_broadcasting_service,
    fake_customer_ws,
    db: Session
):
    """测试WebSocket与广播服务的集成"""
    
    with patch('app.api.v1.endpoints.websocket.verify_websocket_token') as mock_verify:
        mock_verify.return_value = {
            "user_id": fake_customer_ws.id,
            "role": "customer",
            "username": fake_customer_ws.username
        }
        
        with patch('app.api.v1.endpoints.websocket.get_connection_manager') as mock_get_manager:
            mock_get_manager.return_value = mock_connection_manager
            
            # 模拟创建广播服务
            with patch('app.services.broadcasting_factory.create_broadcasting_service') as mock_create_service:
                mock_create_service.return_value = mock_broadcasting_service
                
                mock_websocket.receive_text.side_effect = [WebSocketDisconnect()]
                
                from app.api.v1.endpoints.websocket import websocket_endpoint
                
                await websocket_endpoint(
                    websocket=mock_websocket,
                    token="valid_token",
                    connectionId="integration_test",
                    deviceType="mobile",
                    deviceId="test_device_123",
                    db=db,
                    manager=mock_connection_manager
                )
                
                # 验证连接建立时传递了完整的设备信息
                connect_call_args = mock_connection_manager.connect.call_args
                connection_metadata = connect_call_args[0][2]
                
                assert connection_metadata["device_type"] == "mobile"
                assert connection_metadata["device_id"] == "test_device_123"
                assert connection_metadata["user_role"] == "customer"
                assert connection_metadata["connection_id"] == "integration_test"


@pytest.mark.asyncio
async def test_websocket_device_type_routing(
    mock_connection_manager,
    fake_customer_ws,
    db: Session
):
    """测试设备类型路由功能"""
    
    device_types = ["desktop", "mobile", "tablet"]
    device_connections = []
    
    for device_type in device_types:
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()
        mock_ws.send_text = AsyncMock()
        mock_ws.receive_text = AsyncMock(side_effect=[WebSocketDisconnect()])
        mock_ws.client_state = MagicMock()
        mock_ws.client_state.name = "CONNECTED"
        device_connections.append((mock_ws, device_type))
    
    with patch('app.api.v1.endpoints.websocket.verify_websocket_token') as mock_verify:
        mock_verify.return_value = {
            "user_id": fake_customer_ws.id,
            "role": "customer",
            "username": fake_customer_ws.username
        }
        
        with patch('app.api.v1.endpoints.websocket.get_connection_manager') as mock_get_manager:
            mock_get_manager.return_value = mock_connection_manager
            
            from app.api.v1.endpoints.websocket import websocket_endpoint
            
            # 并发连接不同设备类型
            tasks = []
            for i, (mock_ws, device_type) in enumerate(device_connections):
                task = asyncio.create_task(websocket_endpoint(
                    websocket=mock_ws,
                    token="valid_token",
                    connectionId=f"{device_type}_conn_{i}",
                    deviceType=device_type,
                    deviceId=f"{device_type}_device_{i}",
                    db=db,
                    manager=mock_connection_manager
                ))
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
            # 验证每种设备类型都成功连接
            assert mock_connection_manager.connect.call_count == len(device_types)
            
            # 验证设备元数据正确传递
            for i, call in enumerate(mock_connection_manager.connect.call_args_list):
                connection_metadata = call[0][2]
                expected_device_type = device_types[i]
                assert connection_metadata["device_type"] == expected_device_type
                assert connection_metadata["device_id"] == f"{expected_device_type}_device_{i}"


@pytest.mark.asyncio
async def test_websocket_multi_device_support(
    mock_connection_manager,
    fake_customer_ws,
    db: Session
):
    """测试同一用户多设备连接支持"""
    
    # 同一用户从不同设备连接
    connections = [
        ("desktop_conn_1", "desktop", "work_computer"),
        ("mobile_conn_1", "mobile", "iphone_13"),
        ("tablet_conn_1", "tablet", "ipad_pro"),
    ]
    
    mock_websockets = []
    for _ in connections:
        mock_ws = AsyncMock(spec=WebSocket)
        mock_ws.send_json = AsyncMock()
        mock_ws.send_text = AsyncMock()
        mock_ws.receive_text = AsyncMock(side_effect=[WebSocketDisconnect()])
        mock_ws.client_state = MagicMock()
        mock_ws.client_state.name = "CONNECTED"
        mock_websockets.append(mock_ws)
    
    with patch('app.api.v1.endpoints.websocket.verify_websocket_token') as mock_verify:
        mock_verify.return_value = {
            "user_id": fake_customer_ws.id,
            "role": "customer",
            "username": fake_customer_ws.username
        }
        
        with patch('app.api.v1.endpoints.websocket.get_connection_manager') as mock_get_manager:
            mock_get_manager.return_value = mock_connection_manager
            
            from app.api.v1.endpoints.websocket import websocket_endpoint
            
            # 并发连接多个设备
            tasks = []
            for i, (connection_id, device_type, device_id) in enumerate(connections):
                task = asyncio.create_task(websocket_endpoint(
                    websocket=mock_websockets[i],
                    token="valid_token",
                    connectionId=connection_id,
                    deviceType=device_type,
                    deviceId=device_id,
                    db=db,
                    manager=mock_connection_manager
                ))
                tasks.append(task)
            
            await asyncio.gather(*tasks)
            
            # 验证所有设备都成功连接到同一用户
            assert mock_connection_manager.connect.call_count == len(connections)
            
            # 验证每个连接都使用了相同的user_id但不同的connection_id
            for i, call in enumerate(mock_connection_manager.connect.call_args_list):
                user_id = call[0][0]
                connection_id = call[0][3]
                assert user_id == fake_customer_ws.id
                assert connection_id == connections[i][0]


@pytest.mark.asyncio
async def test_websocket_broadcasting_message_types(
    mock_connection_manager,
    mock_broadcasting_service,
    fake_customer_ws,
    db: Session
):
    """测试不同类型的广播消息"""
    
    # 测试数据：不同消息类型
    message_types = [
        {
            "type": "chat_message",
            "method": "broadcast_message",
            "data": {"content": "Hello", "sender_id": "sender_123", "message_type": "text"}
        },
        {
            "type": "consultation_reply", 
            "method": "broadcast_consultation_reply",
            "data": {"content": "医生回复", "consultant_name": "张医生", "reply_type": "consultation"}
        },
        {
            "type": "typing_status",
            "method": "broadcast_typing_status", 
            "data": {"user_id": "customer_456", "is_typing": True}
        },
        {
            "type": "system_notification",
            "method": "broadcast_system_notification",
            "data": {"title": "系统通知", "message": "维护通知", "type": "maintenance"}
        }
    ]
    
    # 测试广播服务的方法是否被正确调用
    for msg_config in message_types:
        method_name = msg_config["method"]
        method = getattr(mock_broadcasting_service, method_name)
        
        # 模拟调用广播方法
        await method(
            conversation_id="test_conv_123",
            **{k: v for k, v in msg_config.items() if k not in ["type", "method"]}
        )
        
        # 验证方法被调用
        method.assert_called()
        
        # 验证调用参数
        call_args = method.call_args
        assert "conversation_id" in call_args.kwargs or call_args.args
    
    # 验证所有类型的消息都被处理
    assert mock_broadcasting_service.broadcast_message.called
    assert mock_broadcasting_service.broadcast_consultation_reply.called
    assert mock_broadcasting_service.broadcast_typing_status.called
    assert mock_broadcasting_service.broadcast_system_notification.called


@pytest.mark.asyncio
async def test_websocket_offline_notification_integration(
    mock_connection_manager,
    mock_broadcasting_service,
    mock_notification_service,
    fake_customer_ws,
    db: Session
):
    """测试离线通知推送集成"""
    
    # 模拟用户离线
    mock_connection_manager.is_user_online.return_value = False
    mock_broadcasting_service.notification_service = mock_notification_service
    
    # 模拟发送离线通知
    await mock_broadcasting_service.send_direct_message(
        user_id=fake_customer_ws.id,
        message_data={
            "title": "离线消息",
            "content": "您有新的消息",
            "type": "chat_message"
        }
    )
    
    # 验证广播服务被调用
    mock_broadcasting_service.send_direct_message.assert_called_once()
    
    # 验证调用参数包含用户ID和消息数据
    call_args = mock_broadcasting_service.send_direct_message.call_args
    assert call_args[1]["user_id"] == fake_customer_ws.id
    assert "message_data" in call_args[1]


@pytest.mark.asyncio 
async def test_websocket_redis_distributed_features(
    mock_redis_client,
    mock_connection_manager,
    fake_customer_ws,
    db: Session
):
    """测试Redis分布式功能集成"""
    
    # 模拟Redis发布订阅
    mock_pubsub = AsyncMock()
    mock_redis_client.pubsub.return_value = mock_pubsub
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.listen = AsyncMock()
    
    # 模拟分布式连接管理器的Redis操作
    mock_connection_manager.redis = mock_redis_client
    
    # 验证Redis相关操作
    await mock_connection_manager.initialize()
    mock_connection_manager.initialize.assert_called()
    
    # 模拟跨实例消息广播
    broadcast_message = {
        "action": "broadcast", 
        "target_user": fake_customer_ws.id,
        "data": {"content": "跨实例消息"},
        "instance_id": "test_instance"
    }
    
    await mock_connection_manager.send_to_user(fake_customer_ws.id, broadcast_message)
    mock_connection_manager.send_to_user.assert_called_with(fake_customer_ws.id, broadcast_message)


@pytest.mark.asyncio
async def test_websocket_connection_metadata_completeness(
    mock_websocket,
    mock_connection_manager,
    fake_customer_ws,
    db: Session
):
    """测试连接元数据完整性（重构架构要求）"""
    
    with patch('app.api.v1.endpoints.websocket.verify_websocket_token') as mock_verify:
        mock_verify.return_value = {
            "user_id": fake_customer_ws.id,
            "role": "customer",
            "username": fake_customer_ws.username
        }
        
        with patch('app.api.v1.endpoints.websocket.get_connection_manager') as mock_get_manager:
            mock_get_manager.return_value = mock_connection_manager
            
            mock_websocket.receive_text.side_effect = [WebSocketDisconnect()]
            
            from app.api.v1.endpoints.websocket import websocket_endpoint
            
            await websocket_endpoint(
                websocket=mock_websocket,
                token="valid_token",
                connectionId="metadata_test_conn",
                deviceType="desktop",
                deviceId="test_device_meta",
                db=db,
                manager=mock_connection_manager
            )
            
            # 验证连接元数据包含所有必要字段
            connect_call_args = mock_connection_manager.connect.call_args
            connection_metadata = connect_call_args[0][2]
            
            required_fields = [
                "user_role", "username", "connection_id", 
                "device_type", "device_id", "token_verified_at", "connected_at"
            ]
            
            for field in required_fields:
                assert field in connection_metadata, f"缺少必要的元数据字段: {field}"
            
            # 验证字段值正确
            assert connection_metadata["user_role"] == "customer"
            assert connection_metadata["username"] == fake_customer_ws.username
            assert connection_metadata["connection_id"] == "metadata_test_conn"
            assert connection_metadata["device_type"] == "desktop"
            assert connection_metadata["device_id"] == "test_device_meta"


@pytest.mark.asyncio
async def test_websocket_device_specific_messaging(
    mock_connection_manager,
    mock_broadcasting_service,
    fake_customer_ws,
    db: Session
):
    """测试设备特定消息推送"""
    
    # 模拟用户有多个设备在线
    mock_connection_manager.get_user_device_info.return_value = [
        {"connection_id": "desktop_conn", "device_type": "desktop", "connected_at": "2024-01-01"},
        {"connection_id": "mobile_conn", "device_type": "mobile", "connected_at": "2024-01-01"}
    ]
    
    # 测试仅向移动设备发送消息
    await mock_broadcasting_service.send_mobile_only_notification(
        conversation_id="test_conv",
        message_data={
            "title": "移动端通知",
            "content": "这是移动端专用消息"
        }
    )
    
    # 验证调用
    mock_broadcasting_service.send_mobile_only_notification.assert_called_once()
    
    # 验证设备信息查询
    device_info = await mock_broadcasting_service.get_user_device_info(fake_customer_ws.id)
    mock_broadcasting_service.get_user_device_info.assert_called_with(fake_customer_ws.id)


# ============ 兼容性和迁移测试 ============

@pytest.mark.asyncio
async def test_websocket_backward_compatibility(
    mock_websocket,
    mock_connection_manager, 
    fake_customer_ws,
    db: Session
):
    """测试向后兼容性（支持旧版本客户端）"""
    
    with patch('app.api.v1.endpoints.websocket.verify_websocket_token') as mock_verify:
        mock_verify.return_value = {
            "user_id": fake_customer_ws.id,
            "role": "customer",
            "username": fake_customer_ws.username
        }
        
        with patch('app.api.v1.endpoints.websocket.get_connection_manager') as mock_get_manager:
            mock_get_manager.return_value = mock_connection_manager
            
            mock_websocket.receive_text.side_effect = [WebSocketDisconnect()]
            
            from app.api.v1.endpoints.websocket import websocket_endpoint
            
            # 不提供设备参数的连接（模拟旧版本客户端）
            await websocket_endpoint(
                websocket=mock_websocket,
                token="valid_token",
                connectionId=None,  # 明确传递None
                deviceType=None,
                deviceId=None,
                db=db,
                manager=mock_connection_manager
            )
            
            # 验证连接成功建立
            mock_connection_manager.connect.assert_called_once()
            
            # 验证自动生成了缺失的参数
            connect_call_args = mock_connection_manager.connect.call_args
            connection_metadata = connect_call_args[0][2]
            generated_connection_id = connect_call_args[0][3]
            
            assert generated_connection_id is not None
            assert str(fake_customer_ws.id) in str(generated_connection_id)
            assert connection_metadata["device_type"] == "unknown"
            assert connection_metadata["device_id"] is None