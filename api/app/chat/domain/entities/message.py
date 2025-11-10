"""
消息聚合根 - 领域层
包含消息的业务逻辑和验证规则
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.common.infrastructure.db.uuid_utils import message_id


class MessageEntity:
    """消息聚合根"""
    
    def __init__(
        self,
        id: str,
        conversationId: str,
        content: Dict[str, Any],
        messageType: str,
        senderId: Optional[str] = None,
        senderDigitalHumanId: Optional[str] = None,
        senderType: str = "user",
        isImportant: bool = False,
        replyToMessageId: Optional[str] = None,
        reactions: Optional[Dict[str, List[str]]] = None,
        extraMetadata: Optional[Dict[str, Any]] = None,
        requiresConfirmation: bool = False,
        createdAt: Optional[datetime] = None,
        updatedAt: Optional[datetime] = None,
        isRead: bool = False,
        isDeleted: bool = False,
        deletedAt: Optional[datetime] = None,
        deletedBy: Optional[str] = None
    ):
        self.id = id
        self.conversationId = conversationId
        self.content = content
        self.messageType = messageType
        self.senderId = senderId
        self.senderDigitalHumanId = senderDigitalHumanId
        self.senderType = senderType
        self.isImportant = isImportant
        self.replyToMessageId = replyToMessageId
        self.reactions = reactions or {}
        self.extraMetadata = extraMetadata or {}
        self.requiresConfirmation = requiresConfirmation
        self.createdAt = createdAt or datetime.utcnow()
        self.updatedAt = updatedAt or datetime.utcnow()
        self.isRead = isRead
        self.isDeleted = isDeleted
        self.deletedAt = deletedAt
        self.deletedBy = deletedBy
        
        # 验证业务规则
        self._validate()
    
    def _validate(self) -> None:
        """验证业务规则"""
        if not self.conversationId:
            raise ValueError("会话ID不能为空")
        
        if not self.content:
            raise ValueError("消息内容不能为空")
        
        if self.messageType not in ["text", "media", "system", "structured"]:
            raise ValueError("无效的消息类型")
        
        if self.senderType not in ["customer", "consultant", "doctor", "ai", "system", "digital_human"]:
            raise ValueError("无效的发送者类型")
        
        # 系统消息不需要发送者ID
        if self.senderType != "system" and not self.senderId and not self.senderDigitalHumanId:
            raise ValueError("非系统消息必须指定发送者")
    
    def mark_as_read(self) -> None:
        """标记消息为已读"""
        self.isRead = True
        self.updatedAt = datetime.utcnow()
    
    def mark_as_important(self, is_important: bool) -> None:
        """标记消息为重点"""
        self.isImportant = is_important
        self.updatedAt = datetime.utcnow()
    
    def add_reaction(self, user_id: str, emoji: str) -> bool:
        """添加反应"""
        if not emoji:
            return False
        
        if emoji not in self.reactions:
            self.reactions[emoji] = []
        
        if user_id not in self.reactions[emoji]:
            self.reactions[emoji].append(user_id)
            self.updatedAt = datetime.utcnow()
            return True
        
        return False
    
    def remove_reaction(self, user_id: str, emoji: str) -> bool:
        """移除反应"""
        if emoji in self.reactions and user_id in self.reactions[emoji]:
            self.reactions[emoji].remove(user_id)
            
            # 如果没有用户使用此反应，删除整个反应
            if not self.reactions[emoji]:
                del self.reactions[emoji]
            
            self.updatedAt = datetime.utcnow()
            return True
        
        return False
    
    def delete(self, deleted_by: str) -> None:
        """软删除消息"""
        self.isDeleted = True
        self.deletedAt = datetime.utcnow()
        self.deletedBy = deleted_by
        self.updatedAt = datetime.utcnow()
    
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
    ) -> "MessageEntity":
        """创建文本消息"""
        if not text.strip():
            raise ValueError("文本内容不能为空")
        
        content = {"text": text.strip()}
        
        return cls(
            id=message_id(),
            conversationId=conversation_id,
            content=content,
            messageType="text",
            senderId=sender_id,
            senderDigitalHumanId=sender_digital_human_id,
            senderType=sender_type,
            isImportant=is_important,
            replyToMessageId=reply_to_message_id,
            extraMetadata=extra_metadata
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
    ) -> "MessageEntity":
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
            conversationId=conversation_id,
            content=content,
            messageType="media",
            senderId=sender_id,
            senderType=sender_type,
            isImportant=is_important,
            replyToMessageId=reply_to_message_id
        )
    
    @classmethod
    def create_system_event_message(
        cls,
        conversation_id: str,
        event_type: str,
        status: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None
    ) -> "MessageEntity":
        """创建系统事件消息"""
        content = {
            "event_type": event_type,
            "status": status,
            **(event_data or {})
        }
        
        return cls(
            id=message_id(),
            conversationId=conversation_id,
            content=content,
            messageType="system",
            senderType="system"
        )
    
    # 兼容旧的蛇形命名访问
    @property
    def conversation_id(self) -> str:
        return self.conversationId
    
    @conversation_id.setter
    def conversation_id(self, value: str) -> None:
        self.conversationId = value
    
    @property
    def message_type(self) -> str:
        return self.messageType
    
    @message_type.setter
    def message_type(self, value: str) -> None:
        self.messageType = value
    
    @property
    def sender_id(self) -> Optional[str]:
        return self.senderId
    
    @sender_id.setter
    def sender_id(self, value: Optional[str]) -> None:
        self.senderId = value
    
    @property
    def sender_digital_human_id(self) -> Optional[str]:
        return self.senderDigitalHumanId
    
    @sender_digital_human_id.setter
    def sender_digital_human_id(self, value: Optional[str]) -> None:
        self.senderDigitalHumanId = value
    
    @property
    def sender_type(self) -> str:
        return self.senderType
    
    @sender_type.setter
    def sender_type(self, value: str) -> None:
        self.senderType = value
    
    @property
    def is_important(self) -> bool:
        return self.isImportant
    
    @is_important.setter
    def is_important(self, value: bool) -> None:
        self.isImportant = value
    
    @property
    def reply_to_message_id(self) -> Optional[str]:
        return self.replyToMessageId
    
    @reply_to_message_id.setter
    def reply_to_message_id(self, value: Optional[str]) -> None:
        self.replyToMessageId = value
    
    @property
    def extra_metadata(self) -> Dict[str, Any]:
        return self.extraMetadata
    
    @extra_metadata.setter
    def extra_metadata(self, value: Optional[Dict[str, Any]]) -> None:
        self.extraMetadata = value or {}
    
    @property
    def requires_confirmation(self) -> bool:
        return self.requiresConfirmation
    
    @requires_confirmation.setter
    def requires_confirmation(self, value: bool) -> None:
        self.requiresConfirmation = value
    
    @property
    def created_at(self) -> datetime:
        return self.createdAt
    
    @created_at.setter
    def created_at(self, value: datetime) -> None:
        self.createdAt = value
    
    @property
    def updated_at(self) -> datetime:
        return self.updatedAt
    
    @updated_at.setter
    def updated_at(self, value: datetime) -> None:
        self.updatedAt = value
    
    @property
    def is_read(self) -> bool:
        return self.isRead
    
    @is_read.setter
    def is_read(self, value: bool) -> None:
        self.isRead = value
    
    @property
    def is_deleted(self) -> bool:
        return self.isDeleted
    
    @is_deleted.setter
    def is_deleted(self, value: bool) -> None:
        self.isDeleted = value
    
    @property
    def deleted_at(self) -> Optional[datetime]:
        return self.deletedAt
    
    @deleted_at.setter
    def deleted_at(self, value: Optional[datetime]) -> None:
        self.deletedAt = value
    
    @property
    def deleted_by(self) -> Optional[str]:
        return self.deletedBy
    
    @deleted_by.setter
    def deleted_by(self, value: Optional[str]) -> None:
        self.deletedBy = value
    
    def __str__(self) -> str:
        return (
            f"MessageEntity(id={self.id}, conversationId={self.conversationId}, messageType={self.messageType}, "
            f"senderId={self.senderId}, senderType={self.senderType}, isImportant={self.isImportant}, "
            f"isRead={self.isRead}, isDeleted={self.isDeleted}, createdAt={self.createdAt}, updatedAt={self.updatedAt})"
        )
    
    def __repr__(self) -> str:
        return (
            f"MessageEntity(id={self.id}, conversationId={self.conversationId}, content={self.content}, "
            f"messageType={self.messageType}, senderId={self.senderId}, senderDigitalHumanId={self.senderDigitalHumanId}, "
            f"senderType={self.senderType}, isImportant={self.isImportant}, replyToMessageId={self.replyToMessageId}, "
            f"reactions={self.reactions}, requiresConfirmation={self.requiresConfirmation}, "
            f"isRead={self.isRead}, isDeleted={self.isDeleted}, deletedAt={self.deletedAt}, "
            f"deletedBy={self.deletedBy}, extraMetadata={self.extraMetadata}, createdAt={self.createdAt}, "
            f"updatedAt={self.updatedAt})"
        )
