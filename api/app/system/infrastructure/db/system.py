from sqlalchemy import Column, String, Boolean, JSON

from app.common.infrastructure.db.base_model import BaseModel
from app.common.infrastructure.db.uuid_utils import system_id


class SystemSettings(BaseModel):
    """系统设置数据库模型，存储全局系统配置"""
    __tablename__ = "system_settings"
    __table_args__ = {"comment": "系统设置表，存储全局系统配置"}

    id = Column(String(36), primary_key=True, default=system_id, comment="系统设置ID")
    # 统一使用snake_case命名
    site_name = Column(String(255), nullable=False, default="安美智能咨询系统", comment="站点名称")
    logo_url = Column(String(1024), nullable=True, default="/logo.png", comment="站点Logo URL")
    default_model_id = Column(String(255), nullable=True, comment="默认AI模型ID")
    maintenance_mode = Column(Boolean, default=False, nullable=False, comment="维护模式开关")
    user_registration_enabled = Column(Boolean, default=True, nullable=False, comment="是否允许用户注册")
