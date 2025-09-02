"""
通用WebSocket端点 - 专注于连接管理和实时推送
Redis配置通过环境变量管理，参考api/env.example
"""
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.common.deps import get_db
from app.identity_access.deps import verify_token
from app.identity_access.infrastructure.db.user import User
from app.websocket import get_websocket_service_dependency

logger = logging.getLogger(__name__)

router = APIRouter()


def verify_websocket_token(token: str, db: Session) -> Optional[dict]:
    """验证WebSocket token并返回用户信息"""
    try:
        # 验证token并获取用户ID
        user_id = verify_token(token)
        if not user_id:
            logger.warning("WebSocket token验证失败：token无效")
            return None
            
        # 查询用户信息
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            logger.warning(f"Token中的用户ID在数据库中不存在: {user_id}")
            return None
        
        # 获取用户角色
        user_role = "customer"  # 默认角色
        if hasattr(user, '_active_role') and user._active_role:
            user_role = user._active_role
        elif user.roles:
            user_role = user.roles[0].name
        
        logger.debug(f"WebSocket token验证成功: user_id={user_id}, role={user_role}")
        return {
            "user_id": user_id,
            "role": user_role,
            "username": user.username
        }
        
    except Exception as e:
        logger.error(f"验证WebSocket token失败: {e}")
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="认证token"),
    connectionId: Optional[str] = Query(None, description="连接标识（用于区分多设备）"),
    deviceType: Optional[str] = Query(None, description="设备类型：desktop/mobile/tablet"),
    deviceId: Optional[str] = Query(None, description="设备唯一标识"),
    db: Session = Depends(get_db),
    service = Depends(get_websocket_service_dependency)
):
    """
    通用WebSocket连接端点
    
    职责：
    1. 验证用户token
    2. 建立WebSocket连接
    3. 注册到分布式连接管理器（支持多设备区分）
    4. 处理连接生命周期（心跳、断开等）
    5. 纯连接层，不涉及业务逻辑（如conversationId等）
    
    业务数据处理：
    - 所有业务相关信息（如conversationId）通过消息payload传递
    - WebSocket仅负责用户级连接管理和设备区分
    """
    # 添加详细的调试日志
    logger.info(f"WebSocket连接请求开始: token_prefix={token[:10] if token else 'None'}..., connectionId={connectionId}, deviceType={deviceType}, deviceId={deviceId}")
    
    user_info = None
    
    try:
        # 验证token并获取用户信息
        logger.debug(f"开始验证WebSocket token: token_prefix={token[:10] if token else 'None'}...")
        user_info = verify_websocket_token(token, db)
        
        if not user_info:
            logger.warning(f"WebSocket token验证失败: token_prefix={token[:10] if token else 'None'}...")
            await websocket.close(code=4001, reason="Invalid credentials")
            return
        
        logger.info(f"WebSocket token验证成功: user_id={user_info['user_id']}, role={user_info['role']}")
        
        user_id = user_info["user_id"]
        user_role = user_info["role"]
        
        # 生成连接标识（如果客户端没有提供）
        if not connectionId:
            import time
            connectionId = f"{user_id}_{deviceType or 'unknown'}_{int(time.time() * 1000)}"
        
        # 准备连接元数据，包含设备信息
        from datetime import datetime
        
        connection_metadata = {
            "user_role": user_role,
            "username": user_info["username"],
            "connection_id": connectionId,
            "device_type": deviceType or "unknown",
            "device_id": deviceId,
            "token_verified_at": datetime.now().isoformat(),
            "connected_at": datetime.now().isoformat()
        }
        
        # 建立连接，使用连接标识区分设备
        success = await service.connect_user(user_id, websocket, connection_metadata, connectionId)
        if not success:
            await websocket.close(code=4002, reason="Connection failed")
            return
        
        logger.info(f"WebSocket连接已建立: user_id={user_id}, role={user_role}, device={deviceType}, connection_id={connectionId}")
        
        # 发送连接确认
        await websocket.send_json({
            "event": "connected",
            "data": {
                "user_id": user_id,
                "user_role": user_role,
                "connection_id": connectionId,
                "device_type": deviceType,
                "device_id": deviceId,
                "status": "connected"
            },
            "timestamp": datetime.now().isoformat()
        })
        
        # 保持连接并处理心跳
        while True:
            try:
                # 接收客户端消息（主要用于心跳）
                message = await websocket.receive_text()
                
                # 处理心跳消息
                if message == "ping":
                    await websocket.send_text("pong")
                    logger.debug(f"心跳响应已发送: user_id={user_id}")
                else:
                    # 对于非心跳消息，记录并忽略
                    # 所有业务逻辑消息都应该通过HTTP API处理
                    logger.debug(f"收到非心跳消息，已忽略: user_id={user_id}, message={message[:50]}")
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket客户端主动断开: user_id={user_id}")
                break
            except Exception as e:
                logger.error(f"处理WebSocket消息失败: user_id={user_id}, error={e}")
                # 发送错误响应但不断开连接
                await websocket.send_json({
                    "event": "error",
                    "data": {"message": "消息处理失败"},
                    "timestamp": datetime.now().isoformat()
                })
    
    except Exception as e:
        logger.error(f"WebSocket连接处理失败: {e}")
        if websocket.client_state.name != "DISCONNECTED":
            try:
                await websocket.close(code=4000, reason="Internal error")
            except:
                pass
    
    finally:
        # 清理连接
        if user_info and service:
            try:
                await service.disconnect_user(websocket)
                logger.info(f"WebSocket连接已清理: user_id={user_info['user_id']}")
            except Exception as e:
                logger.error(f"清理WebSocket连接失败: {e}") 