"""
文件服务 - 处理文件上传、存储和管理
遵循扁平化架构，Service层负责业务逻辑和数据库操作
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
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.minio_client = get_minio_client()
    
    def create_file_record(
        self,
        object_name: str,
        file_name: str,
        file_size: int,
        mime_type: str,
        file_type: str,
        user_id: str,
        business_type: Optional[str] = None,
        business_id: Optional[str] = None,
        md5: Optional[str] = None,
        is_public: bool = False,
        db: Optional[Session] = None
    ) -> str:
        """
        创建文件记录
        
        Args:
            object_name: MinIO对象名
            file_name: 原始文件名
            file_size: 文件大小
            mime_type: MIME类型
            file_type: 文件类型
            user_id: 上传用户ID
            business_type: 业务类型
            business_id: 关联业务对象ID
            md5: MD5校验值
            db: 数据库会话
            
        Returns:
            文件ID
        """
        db = db or self.db
        if not db:
            raise HTTPException(status_code=500, detail="数据库会话未初始化")
        
        try:
            from app.common.models.file import File
            
            # 检查是否已存在相同object_name的记录
            existing_file = db.query(File).filter(File.object_name == object_name).first()
            if existing_file:
                logger.info(f"文件记录已存在: {existing_file.id}, object_name={object_name}")
                return existing_file.id
            
            # 创建新文件记录
            file_record = File(
                object_name=object_name,
                file_name=file_name,
                file_size=file_size,
                mime_type=mime_type,
                file_type=file_type,
                user_id=user_id,
                business_type=business_type,
                business_id=business_id,
                md5=md5,
                is_public=is_public,
            )
            
            db.add(file_record)
            db.commit()
            db.refresh(file_record)
            
            logger.info(f"文件记录创建成功: file_id={file_record.id}, object_name={object_name}")
            return file_record.id
            
        except Exception as e:
            logger.error(f"创建文件记录失败: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"创建文件记录失败: {str(e)}")
    
    def get_file_by_id(self, file_id: str, db: Optional[Session] = None) -> Optional[Dict[str, Any]]:
        """
        根据文件ID获取文件信息
        
        Args:
            file_id: 文件ID
            db: 数据库会话
            
        Returns:
            文件信息字典或None
        """
        db = db or self.db
        if not db:
            return None
        
        try:
            from app.common.models.file import File
            
            file_record = db.query(File).filter(File.id == file_id).first()
            if not file_record:
                return None
            
            return {
                "id": file_record.id,
                "object_name": file_record.object_name,
                "file_name": file_record.file_name,
                "file_size": file_record.file_size,
                "mime_type": file_record.mime_type,
                "file_type": file_record.file_type,
                "user_id": file_record.user_id,
                "business_type": file_record.business_type,
                "business_id": file_record.business_id,
                "md5": file_record.md5,
                "is_public": getattr(file_record, "is_public", False),
                "created_at": file_record.created_at
            }
        except Exception as e:
            logger.error(f"获取文件信息失败: {str(e)}")
            return None
    
    def get_file_stream_by_id(self, file_id: str, db: Optional[Session] = None) -> Optional[Iterator[bytes]]:
        """
        根据文件ID获取文件流
        
        Args:
            file_id: 文件ID
            db: 数据库会话
            
        Returns:
            文件流迭代器或None
        """
        file_record = self.get_file_by_id(file_id, db)
        if file_record:
            return self.get_file_stream(file_record['object_name'])
        return None
    
    def can_access_file_by_id(self, file_id: str, user_id: str, db: Optional[Session] = None) -> bool:
        """
        检查用户是否有权限访问文件（通过文件ID）
        
        Args:
            file_id: 文件ID
            user_id: 用户ID
            db: 数据库会话
            
        Returns:
            是否有权限
        """
        db = db or self.db
        file_record = self.get_file_by_id(file_id, db)
        if not file_record:
            return False

        # 公开文件（例如头像）直接允许访问
        if file_record.get("is_public"):
            return True

        # 文件所有者可以访问
        if file_record.get("user_id") == user_id:
            return True

        # 消息文件：需要有会话访问权限
        if file_record.get("business_type") == "message" and file_record.get("business_id") and db:
            return self.can_access_conversation(str(file_record["business_id"]), user_id, db)

        return False

    def can_delete_file_by_id(self, file_id: str, user_id: str, db: Optional[Session] = None) -> bool:
        """检查用户是否有权限删除文件（通过文件ID）"""
        db = db or self.db
        file_record = self.get_file_by_id(file_id, db)
        if not file_record:
            return False

        # 管理员可以删除任何文件
        if db and self._is_admin(user_id, db):
            return True

        return file_record.get("user_id") == user_id

    def delete_file_by_id(self, file_id: str, user_id: str, db: Optional[Session] = None) -> bool:
        """删除文件（通过文件ID）"""
        db = db or self.db
        if not db:
            raise HTTPException(status_code=500, detail="数据库会话未初始化")

        file_record = self.get_file_by_id(file_id, db)
        if not file_record:
            return False

        if not self.can_delete_file_by_id(file_id=file_id, user_id=user_id, db=db):
            raise HTTPException(status_code=403, detail="无权限删除此文件")

        try:
            from app.common.models.file import File

            # 先删对象存储
            self.minio_client.delete_file(file_record["object_name"])

            # 再删DB记录
            db.query(File).filter(File.id == file_id).delete()
            db.commit()
            return True
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"文件删除失败: {str(e)}", exc_info=True)
            db.rollback()
            raise HTTPException(status_code=500, detail="文件删除失败")
    
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
    
    def can_access_file(self, object_name: str, user_id: str, db: Optional[Session] = None) -> bool:
        """
        检查用户是否有权限访问文件
        
        Args:
            object_name: 文件对象名称
            user_id: 用户ID
            db: 数据库会话（可选，如果未提供则使用 self.db）
            
        Returns:
            是否有权限
        """
        db = db or self.db
        try:
            # 临时文件ID不应该通过后端访问
            if object_name.startswith('temp_'):
                logger.warning(f"尝试访问临时文件ID: {object_name}")
                return False
            
            # URL解码，处理可能的URL编码
            import urllib.parse
            object_name = urllib.parse.unquote(object_name)
            
            # 从object_name解析出用户ID和会话ID
            # 格式：{user_id}/{conversation_id}/{filename}
            path_parts = object_name.split('/')
            if len(path_parts) >= 3:
                file_owner_id = path_parts[0]
                conversation_id = path_parts[1]
                
                logger.debug(f"检查文件访问权限: object_name={object_name}, file_owner_id={file_owner_id}, conversation_id={conversation_id}, user_id={user_id}")
                
                # 文件所有者可以访问
                if file_owner_id == user_id:
                    logger.debug(f"用户是文件所有者，允许访问")
                    return True
                
                # 检查用户是否有权限访问对应的会话
                if db:
                    can_access = self.can_access_conversation(conversation_id, user_id, db)
                    logger.debug(f"会话访问权限检查结果: {can_access}")
                    return can_access
            else:
                logger.warning(f"文件路径格式不正确: {object_name}, 路径部分数量: {len(path_parts)}")
            
            return False
        except Exception as e:
            logger.error(f"检查文件访问权限失败: {str(e)}, object_name={object_name}, user_id={user_id}", exc_info=True)
            return False
    
    def can_delete_file(self, object_name: str, user_id: str, db: Optional[Session] = None) -> bool:
        """
        检查用户是否有权限删除文件
        
        Args:
            object_name: 文件对象名称
            user_id: 用户ID
            db: 数据库会话（可选，如果未提供则使用 self.db）
            
        Returns:
            是否有权限
        """
        db = db or self.db
        try:
            # 管理员可以删除任何文件
            if db and self._is_admin(user_id, db):
                return True
            
            # 从object_name解析出文件所有者
            # 格式：{user_id}/{conversation_id}/{filename}
            path_parts = object_name.split('/')
            if len(path_parts) >= 1:
                file_owner_id = path_parts[0]
                return file_owner_id == user_id
            
            return False
        except Exception as e:
            logger.error(f"检查文件删除权限失败: {str(e)}")
            return False
    
    def can_access_conversation(self, conversation_id: str, user_id: str, db: Optional[Session] = None) -> bool:
        """
        检查用户是否有权限访问会话
        
        Args:
            conversation_id: 会话ID
            user_id: 用户ID
            db: 数据库会话（可选，如果未提供则使用 self.db）
            
        Returns:
            是否有权限
        """
        db = db or self.db
        if not db:
            return False
        try:
            from app.chat.models.chat import Conversation, ConversationParticipant
            
            # 1. 检查是否是会话所有者
            conversation = db.query(Conversation).filter(
                and_(
                    Conversation.id == conversation_id,
                    Conversation.owner_id == user_id
                )
            ).first()
            
            if conversation:
                return True
                
            # 2. 检查是否是会话参与者
            participant = db.query(ConversationParticipant).filter(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.user_id == user_id,
                    ConversationParticipant.is_active == True
                )
            ).first()
            
            if participant:
                return True
                
            # 3. 检查是否是管理员 (可选，根据业务需求)
            if self._is_admin(user_id, db):
                return True
                
            return False
        except Exception as e:
            logger.error(f"检查会话访问权限失败: {str(e)}")
            return False
    
    def _is_admin(self, user_id: str, db: Optional[Session] = None) -> bool:
        """检查用户是否为管理员"""
        db = db or self.db
        if not db:
            return False
        try:
            from app.identity_access.models.user import User
            
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
    
    def get_conversation_files(
        self, 
        conversation_id: str,
        file_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        获取会话中的文件列表
        
        Args:
            conversation_id: 会话ID
            file_type: 文件类型筛选
            limit: 返回数量限制
            offset: 偏移量
            db: 数据库会话（可选，如果未提供则使用 self.db）
            
        Returns:
            文件列表
        """
        db = db or self.db
        if not db:
            return []
        try:
            from app.common.models.file import File

            query = db.query(File).filter(
                and_(
                    File.business_type == "message",
                    File.business_id == conversation_id,
                )
            ).order_by(File.created_at.desc())

            if file_type:
                query = query.filter(File.file_type == file_type)

            records = query.offset(offset).limit(limit).all()

            return [
                {
                    "file_id": r.id,
                    "file_name": r.file_name,
                    "file_size": r.file_size,
                    "file_type": r.file_type,
                    "mime_type": r.mime_type,
                }
                for r in records
            ]
        except Exception as e:
            logger.error(f"获取会话文件列表失败: {str(e)}", exc_info=True)
            return []
    
    def cleanup_orphaned_files(self, db: Optional[Session] = None) -> int:
        """
        清理孤立的文件（没有对应消息记录的文件）
        
        Args:
            db: 数据库会话（可选，如果未提供则使用 self.db）
        
        Returns:
            清理的文件数量
        """
        db = db or self.db
        if not db:
            return 0
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
                    if not self._has_message_record(obj.object_name, db):
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
    
    def _has_message_record(self, object_name: str, db: Optional[Session] = None) -> bool:
        """检查文件是否有对应的消息记录"""
        db = db or self.db
        if not db:
            return True  # 出错时保守处理，不删除文件
        try:
            from app.chat.models.chat import Message
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
            
            # 构建存储路径: {user_id}/{conversation_id}/{unique_filename}
            object_name = f"{user_id}/{conversation_id}/{unique_filename}"
            
            # 读取文件内容
            file_content = await file.read()
            
            # 尝试解析音频元数据
            metadata = {}
            if file_info["category"] == "audio":
                try:
                    import mutagen  # type: ignore[import-untyped]
                    import io
                    
                    # 使用BytesIO包装文件内容，避免影响文件指针
                    audio_file = io.BytesIO(file_content)
                    # 使用文件名帮助mutagen识别格式（如果可能）
                    # mutagen.File 会自动检测格式，这是最可靠的方式
                    try:
                        # 尝试使用文件名帮助识别（如果可用）
                        if file.filename:
                            audio = mutagen.File(audio_file, filename=file.filename)
                        else:
                            audio = mutagen.File(audio_file)
                    except Exception as e:
                        logger.debug(f"mutagen自动检测失败，尝试根据MIME类型处理: {str(e)}")
                        # 如果自动检测失败，尝试根据mime_type使用特定格式
                        audio = None
                        try:
                            if file_info["content_type"] in ["audio/mp3", "audio/mpeg"]:
                                from mutagen.mp3 import MP3  # type: ignore[import-untyped]
                                audio = MP3(audio_file)
                            elif file_info["content_type"] in ["audio/wav", "audio/x-wav"]:
                                # mutagen对WAV的支持可能在不同位置，优先使用File自动检测
                                # 如果必须使用特定格式，可以尝试 mutagen.wave，但类型检查器可能无法识别
                                audio = mutagen.File(audio_file)
                            elif file_info["content_type"] == "audio/ogg":
                                from mutagen.oggvorbis import OggVorbis  # type: ignore[import-untyped]
                                audio = OggVorbis(audio_file)
                        except Exception:
                            # 如果所有尝试都失败，audio保持为None
                            pass
                            
                    if audio and audio.info:
                        metadata['duration_seconds'] = audio.info.length
                        if hasattr(audio.info, 'bitrate'):
                            metadata['bitrate'] = audio.info.bitrate
                        if hasattr(audio.info, 'sample_rate'):
                            metadata['sample_rate'] = audio.info.sample_rate
                        
                        logger.info(f"解析音频元数据成功: {metadata}")
                except Exception as e:
                    logger.warning(f"解析音频元数据失败: {str(e)}")
            
            # 上传到Minio
            file_url = self.minio_client.upload_file_data(
                object_name=object_name,
                file_data=file_content,
                content_type=file_info["content_type"]
            )
            
            logger.info(f"文件上传成功: {file_info['filename']} -> {file_url}")
            
            # 创建文件记录
            file_id = self.create_file_record(
                object_name=object_name,
                file_name=file_info["filename"],
                file_size=file_info["size"],
                mime_type=file_info["content_type"],
                file_type=file_info["category"],
                user_id=user_id,
                business_type="message",
                business_id=conversation_id,
                is_public=False,
            )
            
            # 返回文件信息（用于存储在消息content中）
            return {
                "file_id": file_id,
                "file_name": file_info["filename"],
                "file_size": file_info["size"],
                "file_type": file_info["category"],
                "mime_type": file_info["content_type"],
                "metadata": metadata
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"文件上传失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")

    async def upload_avatar(
        self,
        file: UploadFile,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        上传用户头像/配置类图片（不依赖会话）

        - 仅允许 image 类型
        - 存储路径: {user_id}/avatars/{unique_filename}
        """
        try:
            # 验证文件
            file_info = self.validate_file(file)
            if file_info["category"] != "image":
                raise HTTPException(status_code=400, detail="仅支持上传图片类型文件")

            file_extension = os.path.splitext(file_info["filename"])[1]
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            object_name = f"{user_id}/avatars/{unique_filename}"

            file_content = await file.read()
            file_url = self.minio_client.upload_file_data(
                object_name=object_name,
                file_data=file_content,
                content_type=file_info["content_type"],
            )

            logger.info(f"头像上传成功: {file_info['filename']} -> {file_url}")
            
            # 创建文件记录
            file_id = self.create_file_record(
                object_name=object_name,
                file_name=file_info["filename"],
                file_size=file_info["size"],
                mime_type=file_info["content_type"],
                file_type=file_info["category"],
                user_id=user_id,
                business_type="avatar",
                business_id=user_id,
                is_public=True,
            )

            return {
                "file_id": file_id,
                "file_name": file_info["filename"],
                "file_size": file_info["size"],
                "file_type": file_info["category"],
                "mime_type": file_info["content_type"],
                "metadata": {},
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"头像上传失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"头像上传失败: {str(e)}")

    async def upload_binary_data(
        self,
        data: bytes,
        filename: str,
        conversation_id: str,
        user_id: str,
        mime_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        上传二进制数据到MinIO（适用于渠道入站媒体）
        """
        try:
            if not mime_type:
                mime_type, _ = mimetypes.guess_type(filename)
                mime_type = mime_type or "application/octet-stream"
            
            file_category = self.get_file_category(mime_type)
            
            # 生成唯一文件名
            file_extension = os.path.splitext(filename)[1]
            if not file_extension and mime_type.startswith("image/"):
                file_extension = ".jpg" # 默认图
            
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            object_name = f"{user_id}/{conversation_id}/{unique_filename}"
            
            # 上传到MinIO
            self.minio_client.upload_file_data(
                object_name=object_name,
                file_data=data,
                content_type=mime_type
            )

            logger.info(f"二进制数据上传成功: {filename} -> object_name={object_name}")

            # 创建文件记录（渠道入站也按 message 文件处理）
            file_id = self.create_file_record(
                object_name=object_name,
                file_name=filename,
                file_size=len(data),
                mime_type=mime_type,
                file_type=file_category,
                user_id=user_id,
                business_type="message",
                business_id=conversation_id,
                is_public=False,
            )

            return {
                "file_id": file_id,
                "file_name": filename,
                "file_size": len(data),
                "file_type": file_category,
                "mime_type": mime_type,
                "metadata": {},
            }
        except Exception as e:
            logger.error(f"二进制数据上传失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"文件存储失败")
    
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
    
    def create_upload_session(
        self, 
        upload_id: str,
        file_name: str,
        file_size: int,
        chunk_size: int,
        conversation_id: str,
        user_id: str,
        db: Optional[Session] = None
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
            db: 数据库会话（可选，如果未提供则使用 self.db）
        """
        db = db or self.db
        if not db:
            raise HTTPException(status_code=500, detail="数据库会话未初始化")
        try:
            from app.common.models.upload import UploadSession
            
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
    
    def get_upload_status(self, upload_id: str, db: Optional[Session] = None) -> Dict[str, Any]:
        """
        获取上传状态
        
        Args:
            upload_id: 上传ID
            db: 数据库会话（可选，如果未提供则使用 self.db）
            
        Returns:
            上传状态信息
        """
        db = db or self.db
        if not db:
            return {
                "status": "not_found",
                "uploaded_chunks": 0,
                "total_chunks": 0
            }
        try:
            from app.common.models.upload import UploadSession, UploadChunk
            
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
    
    def upload_chunk(
        self,
        upload_id: str,
        chunk_index: int,
        chunk_data: bytes,
        user_id: str,
        db: Optional[Session] = None
    ) -> bool:
        """
        上传单个分片
        
        Args:
            upload_id: 上传ID
            chunk_index: 分片索引
            chunk_data: 分片数据
            user_id: 用户ID
            db: 数据库会话（可选，如果未提供则使用 self.db）
            
        Returns:
            是否上传成功
        """
        db = db or self.db
        if not db:
            return False
        try:
            from app.common.models.upload import UploadSession, UploadChunk
            
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
    
    def complete_upload(
        self,
        upload_id: str,
        conversation_id: str,
        user_id: str,
        db: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        完成文件上传，合并所有分片
        
        Args:
            upload_id: 上传ID
            conversation_id: 会话ID
            user_id: 用户ID
            db: 数据库会话（可选，如果未提供则使用 self.db）
            
        Returns:
            完整文件信息
        """
        db = db or self.db
        if not db:
            raise HTTPException(status_code=500, detail="数据库会话未初始化")
        try:
            from app.common.models.upload import UploadSession, UploadChunk
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
                final_object_name = f"{user_id}/{conversation_id}/{unique_filename}"
                
                # 上传完整文件到MinIO
                with open(temp_path, 'rb') as temp_file:
                    file_data = temp_file.read()
                
                # 推导文件类型
                mime_type, _ = mimetypes.guess_type(upload_session.file_name)
                if not mime_type:
                    mime_type = "application/octet-stream"
                
                self.minio_client.upload_file_data(
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
                
                logger.info(f"文件合并完成: {upload_session.file_name} -> object_name={final_object_name}")
                
                # 创建文件记录
                file_category = self.get_file_category(mime_type)
                file_id = self.create_file_record(
                    object_name=final_object_name,
                    file_name=upload_session.file_name,
                    file_size=upload_session.file_size,
                    mime_type=mime_type,
                    file_type=file_category,
                    user_id=user_id,
                    business_type="message",
                    business_id=conversation_id,
                    is_public=False,
                )
                
                # 返回文件信息
                return {
                    "file_id": file_id,
                    "file_name": upload_session.file_name,
                    "file_size": upload_session.file_size,
                    "file_type": file_category,
                    "mime_type": mime_type
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
    
    def _cleanup_chunks(self, upload_id: str, db: Optional[Session] = None) -> None:
        """
        清理上传的分片
        
        Args:
            upload_id: 上传ID
            db: 数据库会话（可选，如果未提供则使用 self.db）
        """
        db = db or self.db
        if not db:
            return
        try:
            from app.common.models.upload import UploadChunk
            
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
    
    def cancel_upload(self, upload_id: str, user_id: str, db: Optional[Session] = None) -> bool:
        """
        取消上传
        
        Args:
            upload_id: 上传ID
            user_id: 用户ID
            db: 数据库会话（可选，如果未提供则使用 self.db）
            
        Returns:
            是否取消成功
        """
        db = db or self.db
        if not db:
            return False
        try:
            from app.common.models.upload import UploadSession
            
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