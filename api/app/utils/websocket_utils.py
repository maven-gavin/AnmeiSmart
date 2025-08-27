"""
WebSocket公共工具函数 - 减少代码重复
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def create_websocket_message(
    action: str,
    data: Dict[str, Any],
    conversation_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建标准WebSocket消息格式
    
    Args:
        action: 消息动作类型
        data: 消息数据
        conversation_id: 会话ID（可选）
        **kwargs: 其他字段
    
    Returns:
        Dict[str, Any]: 标准格式的WebSocket消息
    """
    message = {
        "action": action,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    if conversation_id:
        message["conversation_id"] = conversation_id
    
    # 添加其他字段
    message.update(kwargs)
    
    return message


def create_success_response(message: str, **kwargs) -> Dict[str, Any]:
    """创建成功响应"""
    return create_websocket_message(
        action="response",
        data={
            "status": "success",
            "message": message
        },
        **kwargs
    )


def create_error_response(message: str, **kwargs) -> Dict[str, Any]:
    """创建错误响应"""
    return create_websocket_message(
        action="error",
        data={
            "status": "error",
            "message": message
        },
        **kwargs
    )


def create_connection_metadata(
    user_id: str,
    user_role: str,
    username: str,
    connection_id: str,
    device_type: str = "unknown",
    device_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    创建连接元数据
    
    Args:
        user_id: 用户ID
        user_role: 用户角色
        username: 用户名
        connection_id: 连接ID
        device_type: 设备类型
        device_id: 设备ID
        **kwargs: 其他元数据
    
    Returns:
        Dict[str, Any]: 连接元数据
    """
    metadata = {
        "user_id": user_id,
        "user_role": user_role,
        "username": username,
        "connection_id": connection_id,
        "device_type": device_type,
        "device_id": device_id,
        "connected_at": datetime.now().isoformat()
    }
    
    # 添加其他元数据
    metadata.update(kwargs)
    
    return metadata


def validate_websocket_message(data: Dict[str, Any]) -> tuple[bool, str]:
    """
    验证WebSocket消息格式
    
    Args:
        data: 消息数据
    
    Returns:
        tuple[bool, str]: (是否有效, 错误信息)
    """
    if not isinstance(data, dict):
        return False, "数据格式必须是JSON对象"
    
    if "action" not in data:
        return False, "缺少action字段"
    
    action = data.get("action")
    if action == "message":
        message_data = data.get("data", {})
        if not message_data.get("content", "").strip():
            return False, "消息内容不能为空"
    
    return True, ""


def extract_message_content(content: Any, message_type: str = "text") -> str:
    """
    从消息内容中提取文本
    
    Args:
        content: 消息内容
        message_type: 消息类型
    
    Returns:
        str: 提取的文本内容
    """
    if isinstance(content, str):
        return content
    
    if isinstance(content, dict):
        if message_type == "text":
            return content.get("text", "")
        elif message_type == "media":
            media_info = content.get("media_info", {})
            return media_info.get("name", "媒体文件")
        elif message_type == "system":
            return content.get("message", "系统消息")
    
    return str(content)


def get_content_length(content: Any) -> int:
    """
    获取内容长度
    
    Args:
        content: 消息内容
    
    Returns:
        int: 内容长度
    """
    if isinstance(content, str):
        return len(content)
    elif isinstance(content, dict):
        if "text" in content:
            return len(content["text"])
        else:
            return len(str(content))
    else:
        return len(str(content))
