"""
文件服务 - 处理文件上传、存储和管理
遵循DDD架构，Service层负责业务逻辑，返回Schema对象
"""
import os
import uuid
import mimetypes
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
        "audio/mpeg", "audio/wav", "audio/ogg", "audio/mp4", "audio/aac",
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
                    Conversation.customer_id == user_id
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
            return response.stream()
        except Exception as e:
            logger.error(f"获取文件流失败: {str(e)}")
            return None
    
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