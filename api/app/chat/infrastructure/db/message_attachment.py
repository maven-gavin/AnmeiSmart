from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum, Integer, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from typing import Optional

from app.common.infrastructure.db.base_model import BaseModel
from app.common.infrastructure.db.uuid_utils import message_id


class MessageAttachment(BaseModel):
    """消息附件关联表 - 建立Messages与UploadSession的多对多关系"""
    __tablename__ = "message_attachments"
    __table_args__ = (
        Index('idx_message_attachment_message', 'message_id'),
        Index('idx_message_attachment_upload', 'upload_session_id'),
        {"comment": "消息附件表，建立消息与上传文件的多对多关联"}
    )

    id = Column(String(36), primary_key=True, default=message_id, comment="关联ID")
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="CASCADE"), 
                       nullable=False, comment="消息ID")
    upload_session_id = Column(String(64), ForeignKey("upload_sessions.upload_id", ondelete="CASCADE"), 
                              nullable=False, comment="上传会话ID")
    
    # 附件在消息中的显示顺序和元数据
    display_order = Column(Integer, default=0, comment="在消息中的显示顺序")
    display_name = Column(String(255), nullable=True, comment="显示名称（可自定义）")
    description = Column(Text, nullable=True, comment="附件描述")
    
    # 附件类型和用途
    attachment_type = Column(String(50), nullable=False, default="other", comment="附件类型")
    usage_context = Column(String(100), nullable=True, comment="使用场景：avatar、consultation_image等")
    
    # 状态和权限
    is_primary = Column(Boolean, default=False, comment="是否为主要附件")
    is_public = Column(Boolean, default=True, comment="是否公开可见")
    
    # 关联关系
    message = relationship("app.chat.infrastructure.db.chat.Message", back_populates="attachments")
    upload_session = relationship("app.common.infrastructure.db.upload.UploadSession", back_populates="message_attachments")
    
    def __repr__(self):
        return f"<MessageAttachment(message_id={self.message_id}, upload_id={self.upload_session_id})>"
