"""
WebSocket处理器 - 专注于WebSocket消息的解析和路由
"""
import json
import logging
from typing import Dict, Any
from datetime import datetime

from app.core.events import (
    event_bus, EventTypes, create_message_event, 
    create_user_event, create_system_event
)

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """WebSocket消息处理器"""
    
    def __init__(self):
        self.message_handlers = {
            "message": self.handle_message,
            "typing": self.handle_typing,
            "read": self.handle_read,
            "ping": self.handle_ping,
            "connect": self.handle_connect,
            "disconnect": self.handle_disconnect
        }
    
    async def handle_websocket_message(
        self, 
        data: Dict[str, Any], 
        user_id: str, 
        conversation_id: str
    ) -> Dict[str, Any]:
        """处理WebSocket消息的主入口"""
        try:
            action = data.get("action")
            if not action:
                return self.create_error_response("缺少action字段")
            
            handler = self.message_handlers.get(action)
            if not handler:
                return self.create_error_response(f"未知的action: {action}")
            
            return await handler(data, user_id, conversation_id)
            
        except Exception as e:
            logger.error(f"处理WebSocket消息失败: {e}")
            return self.create_error_response(f"处理消息失败: {str(e)}")
    
    async def handle_message(
        self, 
        data: Dict[str, Any], 
        user_id: str, 
        conversation_id: str
    ) -> Dict[str, Any]:
        """处理聊天消息"""
        try:
            message_data = data.get("data", {})
            content = message_data.get("content", "")
            message_type = message_data.get("type", "text")
            sender_type = message_data.get("sender_type", "user")
            is_important = message_data.get("is_important", False)
            reply_to_message_id = message_data.get("reply_to_message_id")
            
            # 验证content内容（支持新的JSON格式）
            if not self._validate_content(content, message_type):
                return self.create_error_response("消息内容不能为空")
            
            # 根据sender_type确定角色
            # 从token或其他方式获取真实的用户角色
            actual_sender_type = sender_type
            
            # 计算内容长度（用于日志）
            content_length = self._get_content_length(content)
            logger.info(f"处理消息: user_id={user_id}, sender_type={actual_sender_type}, content_length={content_length}")
            
            # 创建消息事件，让业务层处理消息保存和后续逻辑
            event = create_message_event(
                conversation_id=conversation_id,
                user_id=user_id,
                content=content,
                message_type=message_type,
                sender_type=actual_sender_type,
                is_important=is_important,
                reply_to_message_id=reply_to_message_id
            )
            
            # 发布事件，让业务层处理
            await event_bus.publish_async(event)
            
            return self.create_success_response("消息已发送")
            
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
            return self.create_error_response(f"发送消息失败: {str(e)}")
    
    def _validate_content(self, content: Any, message_type: str) -> bool:
        """验证消息内容"""
        if not content:
            return False
        
        # 如果是旧格式的字符串，直接验证
        if isinstance(content, str):
            return bool(content.strip())
        
        # 如果是新格式的字典，根据消息类型验证
        if isinstance(content, dict):
            if message_type == "text":
                return bool(content.get("text", "").strip())
            elif message_type == "media":
                return bool(content.get("media_info"))
            elif message_type == "system":
                return bool(content.get("system_event_type"))
        
        return False
    
    def _get_content_length(self, content: Any) -> int:
        """获取内容长度（用于日志）"""
        if isinstance(content, str):
            return len(content)
        elif isinstance(content, dict):
            if "text" in content:
                return len(content["text"])
            else:
                return len(str(content))
        else:
            return len(str(content))
    
    async def handle_typing(
        self, 
        data: Dict[str, Any], 
        user_id: str, 
        conversation_id: str
    ) -> Dict[str, Any]:
        """处理正在输入状态"""
        try:
            typing_data = data.get("data", {})
            is_typing = typing_data.get("is_typing", False)
            
            # 创建输入状态事件
            event = create_user_event(
                EventTypes.CHAT_TYPING,
                user_id=user_id,
                conversation_id=conversation_id,
                is_typing=is_typing
            )
            
            await event_bus.publish_async(event)
            
            return self.create_success_response("输入状态已更新")
            
        except Exception as e:
            logger.error(f"处理输入状态失败: {e}")
            return self.create_error_response(f"更新输入状态失败: {str(e)}")
    
    async def handle_read(
        self, 
        data: Dict[str, Any], 
        user_id: str, 
        conversation_id: str
    ) -> Dict[str, Any]:
        """处理消息已读状态"""
        try:
            read_data = data.get("data", {})
            message_ids = read_data.get("message_ids", [])
            
            if not message_ids:
                return self.create_error_response("缺少message_ids")
            
            # 创建已读事件
            event = create_user_event(
                EventTypes.CHAT_READ,
                user_id=user_id,
                conversation_id=conversation_id,
                message_ids=message_ids
            )
            
            await event_bus.publish_async(event)
            
            return self.create_success_response("已读状态已更新")
            
        except Exception as e:
            logger.error(f"处理已读状态失败: {e}")
            return self.create_error_response(f"更新已读状态失败: {str(e)}")
    
    async def handle_ping(
        self, 
        data: Dict[str, Any], 
        user_id: str, 
        conversation_id: str
    ) -> Dict[str, Any]:
        """处理心跳消息"""
        return {
            "action": "pong",
            "timestamp": datetime.now().isoformat()
        }
    
    async def handle_connect(
        self, 
        data: Dict[str, Any], 
        user_id: str, 
        conversation_id: str
    ) -> Dict[str, Any]:
        """处理连接确认"""
        return {
            "action": "connect",
            "data": {"status": "connected"},
            "conversation_id": conversation_id,
            "timestamp": datetime.now().isoformat()
        }
    
    async def handle_disconnect(
        self, 
        data: Dict[str, Any], 
        user_id: str, 
        conversation_id: str
    ) -> Dict[str, Any]:
        """处理断开连接"""
        # 创建断开连接事件
        event = create_user_event(
            EventTypes.WS_DISCONNECT,
            user_id=user_id,
            conversation_id=conversation_id,
            reason="user_requested"
        )
        
        await event_bus.publish_async(event)
        
        return self.create_success_response("断开连接")
    
    def create_success_response(self, message: str) -> Dict[str, Any]:
        """创建成功响应"""
        return {
            "action": "response",
            "data": {
                "status": "success",
                "message": message
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def create_error_response(self, message: str) -> Dict[str, Any]:
        """创建错误响应"""
        return {
            "action": "error",
            "data": {
                "status": "error",
                "message": message
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def validate_message_data(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """验证消息数据格式"""
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


# 全局WebSocket处理器实例
websocket_handler = WebSocketHandler() 