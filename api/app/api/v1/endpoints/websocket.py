"""
通用WebSocket端点 - 专注于连接管理和实时推送
Redis配置通过环境变量管理，参考api/env.example
"""
import logging
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.distributed_connection_manager import DistributedConnectionManager
from app.core.redis_client import get_redis_client
from app.core.security import verify_token
from app.db.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# 全局连接管理器（将在应用启动时初始化）
connection_manager: Optional[DistributedConnectionManager] = None


def get_connection_manager() -> DistributedConnectionManager:
    """依赖注入：获取连接管理器实例"""
    if connection_manager is None:
        raise HTTPException(status_code=500, detail="连接管理器未初始化")
    return connection_manager


async def verify_websocket_token(token: str, db: Session) -> Optional[dict]:
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
    manager: DistributedConnectionManager = Depends(get_connection_manager)
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
    user_info = None
    
    try:
        # 验证token并获取用户信息
        user_info = await verify_websocket_token(token, db)
        if not user_info:
            await websocket.close(code=4001, reason="Invalid credentials")
            return
        
        user_id = user_info["user_id"]
        user_role = user_info["role"]
        
        # 生成连接标识（如果客户端没有提供）
        if not connectionId:
            import time
            connectionId = f"{user_id}_{deviceType or 'unknown'}_{int(time.time() * 1000)}"
        
        # 准备连接元数据，包含设备信息
        connection_metadata = {
            "user_role": user_role,
            "username": user_info["username"],
            "connection_id": connectionId,
            "device_type": deviceType or "unknown",
            "device_id": deviceId,
            "token_verified_at": "now",
            "connected_at": "now"
        }
        
        # 建立连接，使用连接标识区分设备
        success = await manager.connect(user_id, websocket, connection_metadata, connectionId)
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
            "timestamp": "now"
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
                    "timestamp": "now"
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
        if user_info and manager:
            try:
                await manager.disconnect(websocket)
                logger.info(f"WebSocket连接已清理: user_id={user_info['user_id']}")
            except Exception as e:
                logger.error(f"清理WebSocket连接失败: {e}")


async def initialize_connection_manager(redis_client):
    """初始化连接管理器（在应用启动时调用）"""
    global connection_manager
    try:
        connection_manager = DistributedConnectionManager(redis_client)
        await connection_manager.initialize()
        logger.info("WebSocket连接管理器初始化成功")
    except Exception as e:
        logger.error(f"初始化WebSocket连接管理器失败: {e}")
        raise


async def cleanup_connection_manager():
    """清理连接管理器（在应用关闭时调用）"""
    global connection_manager
    if connection_manager:
        try:
            await connection_manager.cleanup()
            logger.info("WebSocket连接管理器清理完成")
        except Exception as e:
            logger.error(f"清理WebSocket连接管理器失败: {e}")
        finally:
            connection_manager = None 