"""
消息聚合根 - 领域层
包含消息的业务逻辑和验证规则
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.db.uuid_utils import message_id


class Message:
    """消息聚合根"""
    
    def __init__(
        self,
        id: str,
        conversation_id: str,
        content: Dict[str, Any],
        message_type: str,
        sender_id: Optional[str] = None,
        sender_digital_human_id: Optional[str] = None,
        sender_type: str = "user",
        is_important: bool = False,
        reply_to_message_id: Optional[str] = None,
        reactions: Optional[Dict[str, List[str]]] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
        requires_confirmation: bool = False,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None
    ):
        self._id = id
        self._conversation_id = conversation_id
        self._content = content
        self._message_type = message_type
        self._sender_id = sender_id
        self._sender_digital_human_id = sender_digital_human_id
        self._sender_type = sender_type
        self._is_important = is_important
        self._reply_to_message_id = reply_to_message_id
        self._reactions = reactions or {}
        self._extra_metadata = extra_metadata or {}
        self._requires_confirmation = requires_confirmation
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()
        self._is_read = False
        self._is_deleted = False
        self._deleted_at = None
        self._deleted_by = None
        
        # 验证业务规则
        self._validate()
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def conversation_id(self) -> str:
        return self._conversation_id
    
    @property
    def content(self) -> Dict[str, Any]:
        return self._content
    
    @property
    def message_type(self) -> str:
        return self._message_type
    
    @property
    def sender_id(self) -> Optional[str]:
        return self._sender_id
    
    @property
    def sender_digital_human_id(self) -> Optional[str]:
        return self._sender_digital_human_id
    
    @property
    def sender_type(self) -> str:
        return self._sender_type
    
    @property
    def is_important(self) -> bool:
        return self._is_important
    
    @property
    def reply_to_message_id(self) -> Optional[str]:
        return self._reply_to_message_id
    
    @property
    def reactions(self) -> Dict[str, List[str]]:
        return self._reactions
    
    @property
    def extra_metadata(self) -> Dict[str, Any]:
        return self._extra_metadata
    
    @property
    def requires_confirmation(self) -> bool:
        return self._requires_confirmation
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    @property
    def is_read(self) -> bool:
        return self._is_read
    
    @property
    def is_deleted(self) -> bool:
        return self._is_deleted
    
    def _validate(self) -> None:
        """验证业务规则"""
        if not self._conversation_id:
            raise ValueError("会话ID不能为空")
        
        if not self._content:
            raise ValueError("消息内容不能为空")
        
        if self._message_type not in ["text", "media", "system", "structured"]:
            raise ValueError("无效的消息类型")
        
        if self._sender_type not in ["customer", "consultant", "doctor", "ai", "system", "digital_human"]:
            raise ValueError("无效的发送者类型")
        
        # 系统消息不需要发送者ID
        if self._sender_type != "system" and not self._sender_id and not self._sender_digital_human_id:
            raise ValueError("非系统消息必须指定发送者")
    
    def mark_as_read(self) -> None:
        """标记消息为已读"""
        self._is_read = True
        self._updated_at = datetime.now()
    
    def mark_as_important(self, is_important: bool) -> None:
        """标记消息为重点"""
        self._is_important = is_important
        self._updated_at = datetime.now()
    
    def add_reaction(self, user_id: str, emoji: str) -> bool:
        """添加反应"""
        if not emoji:
            return False
        
        if emoji not in self._reactions:
            self._reactions[emoji] = []
        
        if user_id not in self._reactions[emoji]:
            self._reactions[emoji].append(user_id)
            self._updated_at = datetime.now()
            return True
        
        return False
    
    def remove_reaction(self, user_id: str, emoji: str) -> bool:
        """移除反应"""
        if emoji in self._reactions and user_id in self._reactions[emoji]:
            self._reactions[emoji].remove(user_id)
            
            # 如果没有用户使用此反应，删除整个反应
            if not self._reactions[emoji]:
                del self._reactions[emoji]
            
            self._updated_at = datetime.now()
            return True
        
        return False
    
    def delete(self, deleted_by: str) -> None:
        """软删除消息"""
        self._is_deleted = True
        self._deleted_at = datetime.now()
        self._deleted_by = deleted_by
        self._updated_at = datetime.now()
    
    @classmethod
    def create_text_message(
        cls,
        conversation_id: str,
        text: str,
        sender_id: Optional[str] = None,
        sender_digital_human_id: Optional[str] = None,
        sender_type: str = "user",
        is_important: bool = False,
        reply_to_message_id: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> "Message":
        """创建文本消息"""
        if not text.strip():
            raise ValueError("文本内容不能为空")
        
        content = {"text": text.strip()}
        
        return cls(
            id=message_id(),
            conversation_id=conversation_id,
            content=content,
            message_type="text",
            sender_id=sender_id,
            sender_digital_human_id=sender_digital_human_id,
            sender_type=sender_type,
            is_important=is_important,
            reply_to_message_id=reply_to_message_id,
            extra_metadata=extra_metadata
        )
    
    @classmethod
    def create_media_message(
        cls,
        conversation_id: str,
        media_url: str,
        media_name: str,
        mime_type: str,
        size_bytes: int,
        sender_id: str,
        sender_type: str,
        text: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        is_important: bool = False,
        reply_to_message_id: Optional[str] = None
    ) -> "Message":
        """创建媒体消息"""
        if not media_url:
            raise ValueError("媒体URL不能为空")
        
        content = {
            "media_url": media_url,
            "media_name": media_name,
            "mime_type": mime_type,
            "size_bytes": size_bytes,
            "text": text,
            "metadata": metadata or {}
        }
        
        return cls(
            id=message_id(),
            conversation_id=conversation_id,
            content=content,
            message_type="media",
            sender_id=sender_id,
            sender_type=sender_type,
            is_important=is_important,
            reply_to_message_id=reply_to_message_id
        )
    
    @classmethod
    def create_system_event_message(
        cls,
        conversation_id: str,
        event_type: str,
        status: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None
    ) -> "Message":
        """创建系统事件消息"""
        content = {
            "event_type": event_type,
            "status": status,
            **(event_data or {})
        }
        
        return cls(
            id=message_id(),
            conversation_id=conversation_id,
            content=content,
            message_type="system",
            sender_type="system"
        )
