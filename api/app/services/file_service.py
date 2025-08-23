"""
文件服务 - 处理文件上传、存储和管理
遵循DDD架构，Service层负责业务逻辑，返回Schema对象
"""
import os
import uuid
import mimetypes
from datetime import datetime
from typing import Optional, Dict, Any, List, Iterator, IO
from fastapi import UploadFile, HTTPException
import logging
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.minio_client import get_minio_client
from app.db.uuid_utils import message_id
from app.db.base import get_db, with_db

logger = logging.getLogger(__name__)


class FileService:
    """文件服务类"""
    
    # 支持的文件类型配置
    ALLOWED_MIME_TYPES = {
        # 图片
        "image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp",
        # 文档
        "application/pdf", "application/msword", 
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-powerpoint",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/plain", "text/csv",
        # 音频
        "audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4", "audio/aac", "audio/webm", "audio/webm;codecs=opus",
        # 视频
        "video/mp4", "video/mpeg", "video/quicktime", "video/x-msvideo",
        # 压缩文件
        "application/zip", "application/x-rar-compressed", "application/x-7z-compressed"
    }
    
    # 文件大小限制（字节）
    MAX_FILE_SIZES = {
        "image": 10 * 1024 * 1024,     # 10MB
        "document": 50 * 1024 * 1024,   # 50MB
        "audio": 100 * 1024 * 1024,     # 100MB
        "video": 500 * 1024 * 1024,     # 500MB
        "archive": 100 * 1024 * 1024,   # 100MB
        "default": 10 * 1024 * 1024     # 10MB
    }
    
    def __init__(self):
        self.minio_client = get_minio_client()
    
    def get_file_category(self, mime_type: str) -> str:
        """根据MIME类型获取文件分类"""
        if mime_type.startswith("image/"):
            return "image"
        elif mime_type.startswith("audio/"):
            return "audio"
        elif mime_type.startswith("video/"):
            return "video"
        elif mime_type in ["application/zip", "application/x-rar-compressed", "application/x-7z-compressed"]:
            return "archive"
        elif mime_type.startswith("text/") or "document" in mime_type or mime_type == "application/pdf":
            return "document"
        else:
            return "default"
    
    def validate_file(self, file: UploadFile) -> Dict[str, Any]:
        """
        验证上传的文件
        
        Args:
            file: FastAPI UploadFile对象
            
        Returns:
            文件信息字典
            
        Raises:
            HTTPException: 文件验证失败
        """
        # 检查文件是否为空
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")
        
        # 检查文件大小
        file.file.seek(0, 2)  # 移动到文件末尾
        file_size = file.file.tell()
        file.file.seek(0)  # 重置到文件开头
        
        if file_size == 0:
            raise HTTPException(status_code=400, detail="文件不能为空")
        
        # 获取MIME类型
        mime_type = file.content_type
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(file.filename)
            mime_type = mime_type or "application/octet-stream"
        
        # 检查文件类型
        if mime_type not in self.ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件类型: {mime_type}"
            )
        
        # 检查文件大小限制
        file_category = self.get_file_category(mime_type)
        max_size = self.MAX_FILE_SIZES.get(file_category, self.MAX_FILE_SIZES["default"])
        
        if file_size > max_size:
            size_mb = max_size / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超出限制，{file_category}类型文件最大允许 {size_mb}MB"
            )
        
        return {
            "filename": file.filename,
            "content_type": mime_type,
            "size": file_size,
            "category": file_category
        }
    
    def can_access_file(self, object_name: str, user_id: str) -> bool:
        """
        检查用户是否有权限访问文件
        
        Args:
            object_name: 文件对象名称
            user_id: 用户ID
            
        Returns:
            是否有权限
        """
        try:
            # 从object_name解析出会话ID和用户ID
            # 格式：{conversation_id}/{user_id}/{filename}
            path_parts = object_name.split('/')
            if len(path_parts) >= 3:
                conversation_id = path_parts[0]
                file_owner_id = path_parts[1]
                
                # 文件所有者可以访问
                if file_owner_id == user_id:
                    return True
                
                # 检查用户是否有权限访问对应的会话
                return self.can_access_conversation(conversation_id, user_id)
            
            return False
        except Exception as e:
            logger.error(f"检查文件访问权限失败: {str(e)}")
            return False
    
    def can_delete_file(self, object_name: str, user_id: str) -> bool:
        """
        检查用户是否有权限删除文件
        
        Args:
            object_name: 文件对象名称
            user_id: 用户ID
            
        Returns:
            是否有权限
        """
        try:
            # 管理员可以删除任何文件
            if self._is_admin(user_id):
                return True
            
            # 从object_name解析出文件所有者
            path_parts = object_name.split('/')
            if len(path_parts) >= 2:
                file_owner_id = path_parts[1]
                return file_owner_id == user_id
            
            return False
        except Exception as e:
            logger.error(f"检查文件删除权限失败: {str(e)}")
            return False
    
    @with_db
    def can_access_conversation(self, conversation_id: str, user_id: str, db: Session = None) -> bool:
        """
        检查用户是否有权限访问会话
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            是否有权限
        """
        try:
            from app.db.models.chat import Conversation
            
            conversation = db.query(Conversation).filter(
                and_(
                    Conversation.id == conversation_id,
                    Conversation.owner_id == user_id
                )
            ).first()
            
            return conversation is not None
        except Exception as e:
            logger.error(f"检查会话访问权限失败: {str(e)}")
            return False
    
    @with_db
    def _is_admin(self, user_id: str, db: Session = None) -> bool:
        """检查用户是否为管理员"""
        try:
            from app.db.models.user import User
            
            user = db.query(User).filter(User.id == user_id).first()
            return user and user.role == 'admin'
        except Exception as e:
            logger.error(f"检查管理员权限失败: {str(e)}")
            return False
    
    def get_file_stream(self, object_name: str) -> Optional[Iterator[bytes]]:
        """
        获取文件流
        
        Args:
            object_name: 文件对象名称
            
        Returns:
            文件流迭代器
        """
        try:
            response = self.minio_client.client.get_object(
                self.minio_client.bucket_name, 
                object_name
            )
            logger.info(f"成功获取文件流: {object_name}")
            
            # 直接读取全部数据并返回为生成器
            # 这样可以避免流式传输的复杂性问题
            def get_data():
                try:
                    data = response.read()
                    logger.info(f"读取文件数据: {len(data)} bytes, 文件头: {data[:20].hex() if data else 'empty'}")
                    
                    # 分块返回数据
                    chunk_size = 8192  # 8KB chunks
                    for i in range(0, len(data), chunk_size):
                        chunk = data[i:i + chunk_size]
                        yield chunk
                        
                except Exception as e:
                    logger.error(f"读取文件数据失败: {str(e)}")
                    raise
            
            return get_data()
        except Exception as e:
            logger.error(f"获取文件流失败: {str(e)}")
            return None

    def get_file_data(self, object_name: str) -> Optional[bytes]:
        """
        获取完整文件数据（适用于小文件）
        
        Args:
            object_name: 文件对象名称
            
        Returns:
            文件数据字节
        """
        try:
            response = self.minio_client.client.get_object(
                self.minio_client.bucket_name, 
                object_name
            )
            
            data = response.read()
            logger.info(f"读取完整文件数据: {object_name}, 大小: {len(data)} bytes")
            response.close()
            response.release_conn()
            
            return data
        except Exception as e:
            logger.error(f"获取完整文件数据失败: {str(e)}")
            return None

    def should_use_streaming(self, object_name: str) -> bool:
        """
        判断是否应该使用流式传输
        
        Args:
            object_name: 文件对象名称
            
        Returns:
            是否使用流式传输
        """
        try:
            metadata = self.get_file_metadata(object_name)
            if not metadata:
                return True  # 无法获取元数据时默认使用流式
            
            file_size = metadata.get('size', 0)
            content_type = metadata.get('content_type', '')
            
            # 小于5MB的图片和文档使用完整响应
            if file_size < 5 * 1024 * 1024:  # 5MB
                if (content_type.startswith('image/') or 
                    content_type in ['application/pdf', 'text/plain']):
                    return False
            
            # 大文件或音视频文件使用流式传输
            return True
            
        except Exception as e:
            logger.error(f"判断传输方式失败: {str(e)}")
            return True  # 出错时默认使用流式
    
    def get_file_metadata(self, object_name: str) -> Dict[str, Any]:
        """
        获取文件元数据
        
        Args:
            object_name: 文件对象名称
            
        Returns:
            文件元数据
        """
        try:
            stat = self.minio_client.client.stat_object(
                self.minio_client.bucket_name,
                object_name
            )
            
            filename = os.path.basename(object_name)
            
            return {
                "filename": filename,
                "content_type": stat.content_type,
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag
            }
        except Exception as e:
            logger.error(f"获取文件元数据失败: {str(e)}")
            return {}
    
    @with_db
    def get_conversation_files(
        self, 
        conversation_id: str,
        file_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        获取会话中的文件列表
        
        Args:
            conversation_id: 会话ID
            file_type: 文件类型筛选
            limit: 返回数量限制
            offset: 偏移量
            db: 数据库会话
            
        Returns:
            文件列表
        """
        try:
            from app.db.models.chat import Message
            import json
            
            # 查询文件类型的消息
            query = db.query(Message).filter(
                and_(
                    Message.conversation_id == conversation_id,
                    Message.type == 'file'
                )
            ).order_by(Message.timestamp.desc())
            
            messages = query.offset(offset).limit(limit).all()
            
            files = []
            for message in messages:
                try:
                    # 解析消息内容中的文件信息
                    if message.content:
                        file_data = json.loads(message.content)
                        
                        # 如果指定了文件类型筛选
                        if file_type and file_data.get('file_type') != file_type:
                            continue
                        
                        files.append({
                            "message_id": message.id,
                            "file_info": file_data,
                            "sender": {
                                "id": message.sender_id,
                                "type": message.sender_type,
                                "name": getattr(message.sender, 'username', '未知用户') if message.sender else '未知用户'
                            },
                            "timestamp": message.timestamp
                        })
                except json.JSONDecodeError:
                    continue
            
            return files
        except Exception as e:
            logger.error(f"获取会话文件列表失败: {str(e)}")
            return []
    
    def cleanup_orphaned_files(self) -> int:
        """
        清理孤立的文件（没有对应消息记录的文件）
        
        Returns:
            清理的文件数量
        """
        try:
            # 获取所有文件对象
            objects = self.minio_client.client.list_objects(
                self.minio_client.bucket_name,
                recursive=True
            )
            
            cleaned_count = 0
            
            for obj in objects:
                try:
                    # 检查文件是否有对应的消息记录
                    if not self._has_message_record(obj.object_name):
                        # 删除孤立文件
                        self.minio_client.client.remove_object(
                            self.minio_client.bucket_name,
                            obj.object_name
                        )
                        cleaned_count += 1
                        logger.info(f"删除孤立文件: {obj.object_name}")
                except Exception as e:
                    logger.error(f"删除孤立文件失败 {obj.object_name}: {str(e)}")
                    continue
            
            return cleaned_count
        except Exception as e:
            logger.error(f"清理孤立文件失败: {str(e)}")
            return 0
    
    @with_db
    def _has_message_record(self, object_name: str, db: Session = None) -> bool:
        """检查文件是否有对应的消息记录"""
        try:
            from app.db.models.chat import Message
            import json
            
            # 查询包含此文件的消息
            messages = db.query(Message).filter(Message.type == 'file').all()
            
            for message in messages:
                try:
                    if message.content:
                        file_data = json.loads(message.content)
                        if file_data.get('object_name') == object_name:
                            return True
                except json.JSONDecodeError:
                    continue
            
            return False
        except Exception as e:
            logger.error(f"检查消息记录失败: {str(e)}")
            return True  # 出错时保守处理，不删除文件

    async def upload_file(
        self, 
        file: UploadFile, 
        conversation_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        上传文件到Minio存储
        
        Args:
            file: 上传的文件
            conversation_id: 会话ID
            user_id: 用户ID
            
        Returns:
            文件信息字典（用于存储在消息content中）
        """
        try:
            # 验证文件
            file_info = self.validate_file(file)
            
            # 生成唯一的文件名
            file_extension = os.path.splitext(file_info["filename"])[1]
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            
            # 构建存储路径: {conversation_id}/{user_id}/{unique_filename}
            object_name = f"{conversation_id}/{user_id}/{unique_filename}"
            
            # 读取文件内容
            file_content = await file.read()
            
            # 上传到Minio
            file_url = self.minio_client.upload_file_data(
                object_name=object_name,
                file_data=file_content,
                content_type=file_info["content_type"]
            )
            
            logger.info(f"文件上传成功: {file_info['filename']} -> {file_url}")
            
            # 返回文件信息（用于存储在消息content中）
            return {
                "file_url": file_url,
                "file_name": file_info["filename"],
                "file_size": file_info["size"],
                "file_type": file_info["category"],
                "mime_type": file_info["content_type"],
                "object_name": object_name
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")
    
    def delete_file(self, object_name: str) -> bool:
        """
        删除文件
        
        Args:
            object_name: Minio中的对象名称
            
        Returns:
            删除是否成功
        """
        try:
            return self.minio_client.delete_file(object_name)
        except Exception as e:
            logger.error(f"文件删除失败: {str(e)}")
            return False
    
    def get_file_info(self, file_url: str) -> Optional[Dict[str, Any]]:
        """
        从文件URL解析文件信息
        
        Args:
            file_url: 文件URL
            
        Returns:
            文件信息字典或None
        """
        try:
            # 从URL中提取object_name
            if "/chat-files/" in file_url:
                object_name = file_url.split("/chat-files/", 1)[1]
                
                if self.minio_client.file_exists(object_name):
                    filename = os.path.basename(object_name)
                    return {
                        "object_name": object_name,
                        "filename": filename,
                        "exists": True
                    }
            
            return None
        except Exception as e:
            logger.error(f"获取文件信息失败: {str(e)}")
            return None
    
    def get_supported_file_types(self) -> Dict[str, List[str]]:
        """
        获取支持的文件类型列表
        
        Returns:
            按分类组织的文件类型字典
        """
        types_by_category = {
            "image": [],
            "document": [],
            "audio": [],
            "video": [],
            "archive": []
        }
        
        for mime_type in self.ALLOWED_MIME_TYPES:
            category = self.get_file_category(mime_type)
            if category in types_by_category:
                types_by_category[category].append(mime_type)
        
        return types_by_category
    
    # ================== 断点续传相关方法 ==================
    
    @with_db
    def create_upload_session(
        self, 
        upload_id: str,
        file_name: str,
        file_size: int,
        chunk_size: int,
        conversation_id: str,
        user_id: str,
        db: Session = None
    ) -> None:
        """
        创建上传会话
        
        Args:
            upload_id: 上传ID
            file_name: 文件名
            file_size: 文件大小
            chunk_size: 分片大小
            conversation_id: 会话ID
            user_id: 用户ID
            db: 数据库会话
        """
        try:
            from app.db.models.upload import UploadSession
            
            total_chunks = (file_size + chunk_size - 1) // chunk_size
            
            upload_session = UploadSession(
                upload_id=upload_id,
                file_name=file_name,
                file_size=file_size,
                chunk_size=chunk_size,
                total_chunks=total_chunks,
                conversation_id=conversation_id,
                user_id=user_id,
                status='uploading'
            )
            
            db.add(upload_session)
            db.commit()
            
        except Exception as e:
            logger.error(f"创建上传会话失败: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"创建上传会话失败: {str(e)}")
    
    @with_db
    def get_upload_status(self, upload_id: str, db: Session = None) -> Dict[str, Any]:
        """
        获取上传状态
        
        Args:
            upload_id: 上传ID
            db: 数据库会话
            
        Returns:
            上传状态信息
        """
        try:
            from app.db.models.upload import UploadSession, UploadChunk
            
            upload_session = db.query(UploadSession).filter(
                UploadSession.upload_id == upload_id
            ).first()
            
            if not upload_session:
                return {
                    "status": "not_found",
                    "uploaded_chunks": 0,
                    "total_chunks": 0
                }
            
            # 计算已上传的分片数量
            uploaded_count = db.query(UploadChunk).filter(
                UploadChunk.upload_id == upload_id,
                UploadChunk.status == 'completed'
            ).count()
            
            status = "completed" if uploaded_count == upload_session.total_chunks else "uploading"
            
            return {
                "status": status,
                "uploaded_chunks": uploaded_count,
                "total_chunks": upload_session.total_chunks,
                "file_size": upload_session.file_size,
                "created_at": upload_session.created_at
            }
            
        except Exception as e:
            logger.error(f"获取上传状态失败: {str(e)}")
            return {
                "status": "not_found",
                "uploaded_chunks": 0,
                "total_chunks": 0
            }
    
    @with_db
    def upload_chunk(
        self,
        upload_id: str,
        chunk_index: int,
        chunk_data: bytes,
        user_id: str,
        db: Session = None
    ) -> bool:
        """
        上传单个分片
        
        Args:
            upload_id: 上传ID
            chunk_index: 分片索引
            chunk_data: 分片数据
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            是否上传成功
        """
        try:
            from app.db.models.upload import UploadSession, UploadChunk
            
            # 验证上传会话
            upload_session = db.query(UploadSession).filter(
                UploadSession.upload_id == upload_id,
                UploadSession.user_id == user_id
            ).first()
            
            if not upload_session:
                logger.error(f"上传会话不存在或无权限: {upload_id}")
                return False
            
            # 检查分片是否已存在
            existing_chunk = db.query(UploadChunk).filter(
                UploadChunk.upload_id == upload_id,
                UploadChunk.chunk_index == chunk_index
            ).first()
            
            if existing_chunk and existing_chunk.status == 'completed':
                logger.info(f"分片 {chunk_index} 已存在，跳过上传")
                return True
            
            # 构建分片存储路径
            chunk_object_name = f"chunks/{upload_id}/chunk_{chunk_index:06d}"
            
            # 上传分片到MinIO
            chunk_url = self.minio_client.upload_file_data(
                object_name=chunk_object_name,
                file_data=chunk_data,
                content_type="application/octet-stream"
            )
            
            # 记录分片信息
            if existing_chunk:
                existing_chunk.object_name = chunk_object_name
                existing_chunk.chunk_size = len(chunk_data)
                existing_chunk.status = 'completed'
                existing_chunk.updated_at = datetime.now()
            else:
                chunk_record = UploadChunk(
                    upload_id=upload_id,
                    chunk_index=chunk_index,
                    object_name=chunk_object_name,
                    chunk_size=len(chunk_data),
                    status='completed'
                )
                db.add(chunk_record)
            
            db.commit()
            
            logger.info(f"分片 {chunk_index} 上传成功: {chunk_url}")
            return True
            
        except Exception as e:
            logger.error(f"分片上传失败: {str(e)}")
            db.rollback()
            return False
    
    @with_db
    def complete_upload(
        self,
        upload_id: str,
        conversation_id: str,
        user_id: str,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        完成文件上传，合并所有分片
        
        Args:
            upload_id: 上传ID
            conversation_id: 会话ID
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            完整文件信息
        """
        try:
            from app.db.models.upload import UploadSession, UploadChunk
            import tempfile
            import os
            
            # 获取上传会话
            upload_session = db.query(UploadSession).filter(
                UploadSession.upload_id == upload_id,
                UploadSession.user_id == user_id,
                UploadSession.conversation_id == conversation_id
            ).first()
            
            if not upload_session:
                raise HTTPException(status_code=404, detail="上传会话不存在")
            
            # 获取所有已完成的分片
            chunks = db.query(UploadChunk).filter(
                UploadChunk.upload_id == upload_id,
                UploadChunk.status == 'completed'
            ).order_by(UploadChunk.chunk_index).all()
            
            if len(chunks) != upload_session.total_chunks:
                raise HTTPException(
                    status_code=400, 
                    detail=f"分片不完整: {len(chunks)}/{upload_session.total_chunks}"
                )
            
            # 创建临时文件来合并分片
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                temp_path = temp_file.name
                
                # 按顺序合并分片
                for chunk in chunks:
                    try:
                        # 从MinIO下载分片
                        chunk_stream = self.minio_client.client.get_object(
                            self.minio_client.bucket_name,
                            chunk.object_name
                        )
                        
                        # 写入临时文件
                        for data in chunk_stream.stream():
                            temp_file.write(data)
                            
                    except Exception as e:
                        logger.error(f"下载分片 {chunk.chunk_index} 失败: {str(e)}")
                        raise HTTPException(status_code=500, detail=f"合并文件失败")
            
            try:
                # 生成最终文件路径
                file_extension = os.path.splitext(upload_session.file_name)[1]
                unique_filename = f"{uuid.uuid4().hex}{file_extension}"
                final_object_name = f"{conversation_id}/{user_id}/{unique_filename}"
                
                # 上传完整文件到MinIO
                with open(temp_path, 'rb') as temp_file:
                    file_data = temp_file.read()
                
                # 推导文件类型
                mime_type, _ = mimetypes.guess_type(upload_session.file_name)
                if not mime_type:
                    mime_type = "application/octet-stream"
                
                file_url = self.minio_client.upload_file_data(
                    object_name=final_object_name,
                    file_data=file_data,
                    content_type=mime_type
                )
                
                # 清理分片
                self._cleanup_chunks(upload_id, db)
                
                # 更新上传会话状态
                upload_session.status = 'completed'
                upload_session.final_object_name = final_object_name
                upload_session.updated_at = datetime.now()
                db.commit()
                
                logger.info(f"文件合并完成: {upload_session.file_name} -> {file_url}")
                
                # 返回文件信息
                file_category = self.get_file_category(mime_type)
                return {
                    "file_url": file_url,
                    "file_name": upload_session.file_name,
                    "file_size": upload_session.file_size,
                    "file_type": file_category,
                    "mime_type": mime_type,
                    "object_name": final_object_name
                }
                
            finally:
                # 清理临时文件
                try:
                    os.unlink(temp_path)
                except:
                    pass
                    
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"完成上传失败: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"完成上传失败: {str(e)}")
    
    @with_db
    def _cleanup_chunks(self, upload_id: str, db: Session = None) -> None:
        """
        清理上传的分片
        
        Args:
            upload_id: 上传ID
            db: 数据库会话
        """
        try:
            from app.db.models.upload import UploadChunk
            
            chunks = db.query(UploadChunk).filter(
                UploadChunk.upload_id == upload_id
            ).all()
            
            # 删除MinIO中的分片
            for chunk in chunks:
                try:
                    self.minio_client.delete_file(chunk.object_name)
                except Exception as e:
                    logger.warning(f"删除分片失败 {chunk.object_name}: {str(e)}")
            
            # 删除数据库记录
            db.query(UploadChunk).filter(
                UploadChunk.upload_id == upload_id
            ).delete()
            
            db.commit()
            
        except Exception as e:
            logger.error(f"清理分片失败: {str(e)}")
    
    @with_db 
    def cancel_upload(self, upload_id: str, user_id: str, db: Session = None) -> bool:
        """
        取消上传
        
        Args:
            upload_id: 上传ID
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            是否取消成功
        """
        try:
            from app.db.models.upload import UploadSession
            
            upload_session = db.query(UploadSession).filter(
                UploadSession.upload_id == upload_id,
                UploadSession.user_id == user_id
            ).first()
            
            if not upload_session:
                return False
            
            # 清理分片
            self._cleanup_chunks(upload_id, db)
            
            # 删除上传会话
            db.delete(upload_session)
            db.commit()
            
            logger.info(f"上传已取消: {upload_id}")
            return True
            
        except Exception as e:
            logger.error(f"取消上传失败: {str(e)}")
            db.rollback()
            return False 