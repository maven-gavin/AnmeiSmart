"""
Minio客户端配置和工具类
"""
import logging
from functools import lru_cache
from typing import Optional
from minio import Minio
from minio.error import S3Error

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class MinioClient:
    """Minio客户端类"""
    
    def __init__(self):
        settings = get_settings()
        self.client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket_name = settings.MINIO_BUCKET_NAME
        self._ensure_bucket_exists()
    
    def _ensure_bucket_exists(self):
        """确保bucket存在，如果不存在则创建"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"创建Minio bucket: {self.bucket_name}")
            else:
                logger.debug(f"Minio bucket已存在: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"Minio bucket操作失败: {e}")
            raise
    
    def upload_file(self, object_name: str, file_path: str, content_type: str = None) -> str:
        """
        上传文件到Minio
        
        Args:
            object_name: 对象名称（存储路径）
            file_path: 本地文件路径
            content_type: 文件MIME类型
            
        Returns:
            文件访问URL
        """
        try:
            self.client.fput_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                file_path=file_path,
                content_type=content_type
            )
            
            # 生成文件访问URL
            file_url = f"http://{get_settings().MINIO_ENDPOINT}/{self.bucket_name}/{object_name}"
            logger.info(f"文件上传成功: {object_name} -> {file_url}")
            return file_url
            
        except S3Error as e:
            logger.error(f"文件上传失败: {e}")
            raise
    
    def upload_file_data(self, object_name: str, file_data: bytes, content_type: str = None) -> str:
        """
        上传文件数据到Minio
        
        Args:
            object_name: 对象名称（存储路径）
            file_data: 文件字节数据
            content_type: 文件MIME类型
            
        Returns:
            文件访问URL
        """
        try:
            from io import BytesIO
            
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=BytesIO(file_data),
                length=len(file_data),
                content_type=content_type
            )
            
            # 生成文件访问URL
            file_url = f"http://{get_settings().MINIO_ENDPOINT}/{self.bucket_name}/{object_name}"
            logger.info(f"文件数据上传成功: {object_name} -> {file_url}")
            return file_url
            
        except S3Error as e:
            logger.error(f"文件数据上传失败: {e}")
            raise
    
    def delete_file(self, object_name: str) -> bool:
        """
        删除文件
        
        Args:
            object_name: 对象名称（存储路径）
            
        Returns:
            删除是否成功
        """
        try:
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"文件删除成功: {object_name}")
            return True
        except S3Error as e:
            logger.error(f"文件删除失败: {e}")
            return False
    
    def file_exists(self, object_name: str) -> bool:
        """
        检查文件是否存在
        
        Args:
            object_name: 对象名称（存储路径）
            
        Returns:
            文件是否存在
        """
        try:
            self.client.stat_object(self.bucket_name, object_name)
            return True
        except S3Error:
            return False
    
    def get_file_url(self, object_name: str, expires: int = 3600) -> Optional[str]:
        """
        获取文件的预签名URL
        
        Args:
            object_name: 对象名称（存储路径）
            expires: URL有效期（秒）
            
        Returns:
            预签名URL
        """
        try:
            url = self.client.presigned_get_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                expires=expires
            )
            return url
        except S3Error as e:
            logger.error(f"获取预签名URL失败: {e}")
            return None


@lru_cache()
def get_minio_client() -> MinioClient:
    """获取Minio客户端单例"""
    return MinioClient() 