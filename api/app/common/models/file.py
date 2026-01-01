"""
文件表模型 - 统一管理所有文件
"""
from sqlalchemy import Column, String, BigInteger, ForeignKey, Index, Boolean
from app.common.models.base_model import BaseModel
from app.common.deps.uuid_utils import generate_uuid


def file_id() -> str:
    """生成文件ID"""
    return generate_uuid()


class File(BaseModel):
    """文件表 - 统一管理所有文件"""
    __tablename__ = "files"
    __table_args__ = (
        Index('idx_file_user_id', 'user_id'),
        Index('idx_file_business', 'business_type', 'business_id'),
        Index('idx_file_object_name', 'object_name'),
        {"comment": "文件表，统一管理所有文件信息"}
    )

    id = Column(String(36), primary_key=True, default=file_id, comment="文件ID")
    object_name = Column(String(500), nullable=False, unique=True, comment="MinIO对象名")
    file_name = Column(String(255), nullable=False, comment="原始文件名")
    file_size = Column(BigInteger, nullable=False, comment="文件大小（字节）")
    mime_type = Column(String(100), nullable=False, comment="MIME类型")
    file_type = Column(String(50), nullable=False, comment="文件类型：image/document/audio/video/archive")
    md5 = Column(String(50), nullable=True, comment="MD5校验值")
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, comment="上传用户ID")
    business_type = Column(String(50), nullable=True, comment="业务类型：avatar/message/document")
    business_id = Column(String(36), nullable=True, comment="关联业务对象ID")
    is_public = Column(Boolean, default=False, nullable=False, comment="是否公开访问（例如头像）")

    def __repr__(self):
        return f"<File(id={self.id}, file_name={self.file_name}, object_name={self.object_name})>"

