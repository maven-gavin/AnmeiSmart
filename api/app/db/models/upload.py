"""
上传相关的数据库模型
支持断点续传功能
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, BigInteger, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.models.base_model import BaseModel


class UploadSession(BaseModel):
    """
    上传会话模型
    用于跟踪文件的分片上传进度
    """
    __tablename__ = "upload_sessions"
    
    # 基础字段
    upload_id = Column(String(64), unique=True, index=True, nullable=False, comment="上传ID")
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    file_size = Column(BigInteger, nullable=False, comment="文件总大小（字节）")
    chunk_size = Column(Integer, nullable=False, comment="分片大小（字节）")
    total_chunks = Column(Integer, nullable=False, comment="总分片数")
    
    # 关联字段
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, comment="关联会话ID")
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="上传用户ID")
    
    # 状态字段
    status = Column(String(20), default="uploading", comment="上传状态: uploading, completed, failed, cancelled")
    final_object_name = Column(String(500), nullable=True, comment="合并后的文件对象名")
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    user = relationship("User", back_populates="upload_sessions")
    conversation = relationship("Conversation", back_populates="upload_sessions")
    chunks = relationship("UploadChunk", back_populates="upload_session", cascade="all, delete-orphan")


class UploadChunk(BaseModel):
    """
    上传分片模型
    记录每个分片的上传状态和存储位置
    """
    __tablename__ = "upload_chunks"
    
    # 基础字段
    upload_id = Column(String(64), ForeignKey("upload_sessions.upload_id"), nullable=False, comment="关联上传ID")
    chunk_index = Column(Integer, nullable=False, comment="分片索引（从0开始）")
    object_name = Column(String(500), nullable=False, comment="分片在MinIO中的对象名")
    chunk_size = Column(Integer, nullable=False, comment="分片实际大小（字节）")
    
    # 状态字段
    status = Column(String(20), default="uploading", comment="分片状态: uploading, completed, failed")
    checksum = Column(String(64), nullable=True, comment="分片校验和（可选）")
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 关系
    upload_session = relationship("UploadSession", back_populates="chunks")
    
    # 复合唯一索引：同一个上传ID下，分片索引唯一
    __table_args__ = (
        UniqueConstraint('upload_id', 'chunk_index', name='uk_upload_chunk_index'),
        {"comment": "上传分片表，记录每个分片的上传状态和存储位置"},
    ) 