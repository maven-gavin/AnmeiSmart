"""
文件领域Schema
包含文件上传、管理、断点续传等相关的数据模型
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel


class FileInfo(BaseModel):
    """文件信息模型"""
    file_url: str
    file_name: str
    file_size: int
    file_type: str  # image, document, audio, video, archive
    mime_type: str
    object_name: Optional[str] = None


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    success: bool
    message: str
    file_info: Optional[FileInfo] = None


class FileUploadRequest(BaseModel):
    """文件上传请求模型"""
    conversation_id: str


# ================== 断点续传相关Schema ==================

class ChunkUploadRequest(BaseModel):
    """分片上传请求模型"""
    conversation_id: str
    upload_id: str
    chunk_index: int
    total_chunks: int
    chunk_size: int


class UploadStatusResponse(BaseModel):
    """上传状态响应模型"""
    status: Literal["not_found", "uploading", "completed"]
    uploaded_chunks: int
    total_chunks: int
    file_size: Optional[int] = None
    created_at: Optional[datetime] = None


class CompleteUploadRequest(BaseModel):
    """完成上传请求模型"""
    upload_id: str
    file_name: str
    conversation_id: str


class ResumableUploadInfo(BaseModel):
    """断点续传信息模型"""
    upload_id: str
    file_name: str
    file_size: int
    chunk_size: int
    total_chunks: int
    uploaded_chunks: int
    created_at: datetime
    conversation_id: str
    user_id: str


class StartResumableUploadRequest(BaseModel):
    """开始断点续传请求模型"""
    file_name: str
    file_size: int
    chunk_size: int
    conversation_id: str


class StartResumableUploadResponse(BaseModel):
    """开始断点续传响应模型"""
    success: bool
    upload_id: str
    total_chunks: int
    chunk_size: int


class CancelUploadResponse(BaseModel):
    """取消上传响应模型"""
    success: bool
    message: str 