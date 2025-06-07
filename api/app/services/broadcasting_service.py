"""
广播服务 - 统一处理实时消息推送和离线通知
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
from app.core.distributed_connection_manager import DistributedConnectionManager
from app.db.models.chat import Conversation
from app.services.notification_service import NotificationService, get_notification_service

logger = logging.getLogger(__name__)


class BroadcastingService:
    """
    广播服务 - 负责消息的实时推送和离线通知
    
    核心职责：
    1. 检查用户在线状态
    2. 在线用户：通过WebSocket实时推送
    3. 离线用户：调用NotificationService发送推送通知
    4. 处理各种类型的消息广播
    """
    
    def __init__(self, connection_manager: DistributedConnectionManager, db: Session = None, notification_service: NotificationService = None):
        self.connection_manager = connection_manager
        self.db = db  # 用于查询会话参与者
        self.notification_service = notification_service or get_notification_service()
        logger.info("广播服务已初始化，已集成通知推送服务")
    
    async def broadcast_message(self, conversation_id: str, message_data: Dict[str, Any], exclude_user_id: str = None):
        """
        广播聊天消息到会话参与者
        
        Args:
            conversation_id: 会话ID
            message_data: 消息数据，包含完整的消息信息
            exclude_user_id: 要排除的用户ID（通常是发送者）
        """
        try:
            # 获取会话参与者（这里需要根据实际业务逻辑获取）
            participants = await self._get_conversation_participants(conversation_id)
            
            # 构造WebSocket消息格式
            websocket_payload = {
                "event": "new_message",
                "data": message_data,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # 向每个参与者发送消息
            for participant_id in participants:
                if exclude_user_id and participant_id == exclude_user_id:
                    continue
                
                await self._send_to_user_with_fallback(
                    user_id=participant_id,
                    payload=websocket_payload,
                    notification_data={
                        "title": "新消息",
                        "body": self._extract_notification_content(message_data),
                        "conversation_id": conversation_id
                    }
                )
            
            logger.info(f"消息广播完成: conversation_id={conversation_id}, participants={len(participants)}")
            
        except Exception as e:
            logger.error(f"广播消息失败: {e}")
    
    async def broadcast_typing_status(self, conversation_id: str, user_id: str, is_typing: bool):
        """广播正在输入状态"""
        try:
            participants = await self._get_conversation_participants(conversation_id)
            
            typing_payload = {
                "event": "typing_status",
                "data": {
                    "user_id": user_id,
                    "is_typing": is_typing
                },
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # 向会话中的其他用户发送输入状态（排除发送者）
            for participant_id in participants:
                if participant_id != user_id:
                    is_online = await self.connection_manager.is_user_online(participant_id)
                    if is_online:
                        await self.connection_manager.send_to_user(participant_id, typing_payload)
            
            logger.debug(f"输入状态已广播: user_id={user_id}, is_typing={is_typing}")
            
        except Exception as e:
            logger.error(f"广播输入状态失败: {e}")
    
    async def broadcast_read_status(self, conversation_id: str, user_id: str, message_ids: List[str]):
        """广播消息已读状态"""
        try:
            participants = await self._get_conversation_participants(conversation_id)
            
            read_payload = {
                "event": "read_status",
                "data": {
                    "user_id": user_id,
                    "message_ids": message_ids
                },
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
            
            # 向会话中的其他用户发送已读状态（排除读取者）
            for participant_id in participants:
                if participant_id != user_id:
                    is_online = await self.connection_manager.is_user_online(participant_id)
                    if is_online:
                        await self.connection_manager.send_to_user(participant_id, read_payload)
            
            logger.debug(f"已读状态已广播: user_id={user_id}, message_count={len(message_ids)}")
            
        except Exception as e:
            logger.error(f"广播已读状态失败: {e}")
    
    async def broadcast_system_notification(self, conversation_id: str, notification_data: Dict[str, Any], target_user_ids: List[str] = None):
        """广播系统通知"""
        try:
            if target_user_ids is None:
                # 如果没有指定目标用户，广播给会话所有参与者
                target_user_ids = await self._get_conversation_participants(conversation_id)
            
            system_payload = {
                "event": "system_notification",
                "data": notification_data,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
            
            for user_id in target_user_ids:
                await self._send_to_user_with_fallback(
                    user_id=user_id,
                    payload=system_payload,
                    notification_data={
                        "title": notification_data.get("title", "系统通知"),
                        "body": notification_data.get("message", ""),
                        "conversation_id": conversation_id
                    }
                )
            
            logger.info(f"系统通知已广播: conversation_id={conversation_id}, targets={len(target_user_ids)}")
            
        except Exception as e:
            logger.error(f"广播系统通知失败: {e}")
    
    async def send_direct_message(self, user_id: str, message_data: Dict[str, Any]):
        """向指定用户发送直接消息"""
        try:
            direct_payload = {
                "event": "direct_message",
                "data": message_data,
                "timestamp": datetime.now().isoformat()
            }
            
            await self._send_to_user_with_fallback(
                user_id=user_id,
                payload=direct_payload,
                notification_data={
                    "title": message_data.get("title", "新消息"),
                    "body": message_data.get("content", ""),
                }
            )
            
            logger.info(f"直接消息已发送: user_id={user_id}")
            
        except Exception as e:
            logger.error(f"发送直接消息失败: {e}")
    
    async def _send_to_user_with_fallback(self, user_id: str, payload: Dict[str, Any], notification_data: Dict[str, Any] = None, target_device_type: str = None):
        """
        向用户发送消息，支持在线/离线fallback和多设备支持
        
        Args:
            user_id: 目标用户ID
            payload: WebSocket消息负载
            notification_data: 离线推送数据
            target_device_type: 目标设备类型（可选，用于精确推送）
        """
        try:
            # 检查用户是否在线
            is_online = await self.connection_manager.is_user_online(user_id)
            
            if is_online:
                # 在线：通过WebSocket发送
                if target_device_type:
                    # 发送到特定设备类型
                    await self.connection_manager.send_to_device_type(user_id, target_device_type, payload)
                    logger.debug(f"实时消息已发送到设备类型: user_id={user_id}, device_type={target_device_type}")
                else:
                    # 发送到所有设备
                    await self.connection_manager.send_to_user(user_id, payload)
                    logger.debug(f"实时消息已发送到所有设备: user_id={user_id}")
            else:
                # 离线：发送推送通知
                if notification_data:
                    await self._send_push_notification(user_id, notification_data, target_device_type)
                logger.debug(f"离线推送已发送: user_id={user_id}, device_type={target_device_type or 'all'}")
                
        except Exception as e:
            logger.error(f"发送消息失败: user_id={user_id}, error={e}")
    
    async def _send_push_notification(self, user_id: str, notification_data: Dict[str, Any], target_device_type: str = None):
        """
        发送推送通知（离线时使用）
        
        Args:
            user_id: 目标用户ID
            notification_data: 推送通知数据
            target_device_type: 目标设备类型（可选，如mobile、desktop等）
        """
        try:
            # 使用集成的通知推送服务
            if self.notification_service:
                success = await self.notification_service.send_push_notification(
                    user_id=user_id, 
                    notification_data=notification_data,
                    device_type=target_device_type
                )
                
                if success:
                    device_info = f" 到{target_device_type}设备" if target_device_type else ""
                    logger.debug(f"推送通知发送成功{device_info}: user_id={user_id}")
                else:
                    logger.warning(f"推送通知发送失败: user_id={user_id}")
            else:
                logger.warning(f"通知服务未配置，无法发送推送: user_id={user_id}")
            
        except Exception as e:
            logger.error(f"发送推送通知失败: user_id={user_id}, error={e}")
    
    async def _get_conversation_participants(self, conversation_id: str) -> List[str]:
        """
        获取会话参与者列表
        """
        try:
            if not self.db:
                logger.warning("数据库session未注入，无法查询会话参与者")
                return []
            
            # 查询会话信息
            conversation = self.db.query(Conversation).filter(
                Conversation.id == conversation_id
            ).first()
            
            if not conversation:
                logger.warning(f"会话不存在: {conversation_id}")
                return []
            
            participants = []
            
            # 添加客户ID
            if conversation.customer_id:
                participants.append(conversation.customer_id)
            
            # 添加分配的顾问ID
            if conversation.assigned_consultant_id:
                participants.append(conversation.assigned_consultant_id)
            
            logger.debug(f"获取会话参与者: conversation_id={conversation_id}, participants={participants}")
            return participants
            
        except Exception as e:
            logger.error(f"获取会话参与者失败: conversation_id={conversation_id}, error={e}")
            return []
    
    def _extract_notification_content(self, message_data: Dict[str, Any]) -> str:
        """从消息数据中提取推送通知内容"""
        try:
            content = message_data.get("content", "")
            # 截取内容用于推送显示
            max_length = 50
            if len(content) > max_length:
                return content[:max_length] + "..."
            return content
        except Exception:
            return "新消息"
    
    async def send_mobile_only_notification(self, conversation_id: str, message_data: Dict[str, Any], exclude_user_id: str = None):
        """
        只向移动设备发送通知（适合重要消息的移动端推送）
        """
        try:
            participants = await self._get_conversation_participants(conversation_id)
            
            notification_payload = {
                "event": "mobile_notification",
                "data": message_data,
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }
            
            for participant_id in participants:
                if exclude_user_id and participant_id == exclude_user_id:
                    continue
                
                # 只发送给移动设备或离线推送
                await self._send_to_user_with_fallback(
                    user_id=participant_id,
                    payload=notification_payload,
                    target_device_type="mobile",
                    notification_data={
                        "title": message_data.get("title", "重要消息"),
                        "body": self._extract_notification_content(message_data),
                        "conversation_id": conversation_id,
                        "priority": "high"
                    }
                )
            
            logger.info(f"移动端专用通知已发送: conversation_id={conversation_id}")
            
        except Exception as e:
            logger.error(f"发送移动端通知失败: {e}")
    
    async def broadcast_consultation_reply(self, conversation_id: str, reply_data: Dict[str, Any], consultant_id: str):
        """
        广播顾问回复（优化推送策略：桌面端实时，移动端推送）
        """
        try:
            participants = await self._get_conversation_participants(conversation_id)
            
            reply_payload = {
                "event": "consultation_reply",
                "data": reply_data,
                "conversation_id": conversation_id,
                "consultant_id": consultant_id,
                "timestamp": datetime.now().isoformat()
            }
            
            for participant_id in participants:
                if participant_id == consultant_id:
                    continue  # 排除发送者
                
                # 检查用户在线状态
                is_online = await self.connection_manager.is_user_online(participant_id)
                
                if is_online:
                    # 在线用户：发送到所有设备
                    await self.connection_manager.send_to_user(participant_id, reply_payload)
                    logger.debug(f"顾问回复已发送到在线用户: user_id={participant_id}")
                else:
                    # 离线用户：优先推送到移动设备
                    await self._send_push_notification(
                        user_id=participant_id,
                        target_device_type="mobile",
                        notification_data={
                            "title": "顾问回复",
                            "body": self._extract_notification_content(reply_data),
                            "conversation_id": conversation_id,
                            "action": "open_conversation"
                        }
                    )
                    logger.debug(f"顾问回复推送已发送: user_id={participant_id}")
            
            logger.info(f"顾问回复广播完成: conversation_id={conversation_id}, consultant_id={consultant_id}")
            
        except Exception as e:
            logger.error(f"广播顾问回复失败: {e}")
    
    async def get_user_device_info(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户的设备连接信息
        """
        try:
            return self.connection_manager.get_user_devices(user_id)
        except Exception as e:
            logger.error(f"获取用户设备信息失败: user_id={user_id}, error={e}")
            return [] 