from sqlalchemy import Column, String, Boolean, Integer, Text, DateTime, JSON, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from app.common.models.base_model import BaseModel
from app.core.encryption import get_encryption
from typing import Optional, TYPE_CHECKING, cast
import logging

logger = logging.getLogger(__name__)


class MCPToolGroup(BaseModel):
    """MCP工具分组数据库模型 - 支持API密钥加密存储"""
    __tablename__ = "mcp_tool_groups"
    __table_args__ = (
        Index('idx_mcp_groups_enabled', 'enabled'),
        Index('idx_mcp_groups_created_by', 'created_by'),
        Index('idx_mcp_groups_created_at', 'created_at'),
        UniqueConstraint('name', name='uq_mcp_groups_name'),
        UniqueConstraint('api_key', name='uq_mcp_groups_api_key'),
        UniqueConstraint('server_code', name='uq_mcp_groups_server_code'),
        {"comment": "MCP工具分组表，管理API密钥和权限控制"}
    )

    id = Column(String(36), primary_key=True, index=True, comment="分组ID")
    name = Column(String(100), nullable=False, index=True, comment="分组名称")
    description = Column(Text, nullable=True, comment="分组描述")
    _api_key = Column('api_key', String(512), nullable=False, index=True, comment="加密的API密钥")
    hashed_api_key = Column(String(64), nullable=True, index=True, comment="API密钥SHA-256哈希（查询用）")
    server_code = Column(String(32), nullable=True, unique=True, index=True, comment="MCP服务器代码（用于URL路径）")
    user_tier_access = Column(JSON, nullable=False, default=["internal"], comment="允许访问的用户层级")
    allowed_roles = Column(JSON, nullable=False, default=[], comment="允许访问的角色列表")
    enabled = Column(Boolean, nullable=False, default=True, index=True, comment="是否启用")
    created_by = Column(String(36), nullable=True, comment="创建人ID")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")

    # 关联关系
    tools = relationship("MCPTool", back_populates="group", cascade="all, delete-orphan")

    @hybrid_property
    def api_key(self) -> Optional[str]:
        """API密钥的透明解密访问"""
        # 在实例访问时，_api_key已经是实际的字符串值
        api_key_value = cast(Optional[str], self._api_key)
        if not api_key_value:
            return None
        
        try:
            # 检查是否为明文密钥（向后兼容）
            if api_key_value.startswith('mcp_key_'):
                # 已经是明文密钥，直接返回
                return api_key_value
                
            # 尝试解密
            encryption_manager = get_encryption()
            return encryption_manager.decrypt(api_key_value)
            
        except Exception as e:
            logger.warning(f"API密钥解密失败，返回原值: {e}")
            # 如果解密失败，可能是未加密的旧数据，直接返回
            return api_key_value

    @api_key.setter
    def api_key(self, value: Optional[str]) -> None:
        """API密钥的透明加密存储"""
        if not value:
            self._api_key = None
            return
        
        try:
            encryption_manager = get_encryption()
            self._api_key = encryption_manager.encrypt(value)
        except Exception as e:
            logger.error(f"API密钥加密失败，存储原值: {e}")
            self._api_key = value

    def set_api_key_raw(self, encrypted_value: Optional[str]) -> None:
        """直接设置已加密的API密钥（用于数据库迁移等场景）"""
        self._api_key = encrypted_value

    def get_api_key_encrypted(self) -> Optional[str]:
        """获取加密后的API密钥"""
        return cast(Optional[str], self._api_key)

    def __repr__(self):
        return f"<MCPToolGroup(id={self.id}, name={self.name}, enabled={self.enabled})>"


class MCPTool(BaseModel):
    """MCP工具数据库模型"""
    __tablename__ = "mcp_tools"
    __table_args__ = (
        Index('idx_mcp_tools_group_enabled', 'group_id', 'enabled'),
        Index('idx_mcp_tools_tool_name', 'tool_name'),
        Index('idx_mcp_tools_created_at', 'created_at'),
        UniqueConstraint('group_id', 'tool_name', name='uq_mcp_tools_group_tool_name'),
        {"comment": "MCP工具表，存储工具配置和元数据"}
    )

    id = Column(String(36), primary_key=True, index=True, comment="工具ID")
    group_id = Column(String(36), ForeignKey("mcp_tool_groups.id", ondelete="CASCADE"), nullable=False, index=True, comment="所属分组ID")
    tool_name = Column(String(100), nullable=False, index=True, comment="工具名称")
    description = Column(Text, nullable=True, comment="工具描述")
    version = Column(String(20), nullable=False, default="1.0.0", comment="工具版本")
    enabled = Column(Boolean, nullable=False, default=True, index=True, comment="是否启用")
    timeout_seconds = Column(Integer, nullable=False, default=30, comment="超时时间（秒）")
    config_data = Column(JSON, nullable=True, comment="工具配置数据", default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间")

    # 关联关系
    group = relationship("MCPToolGroup", back_populates="tools")

    def __repr__(self):
        return f"<MCPTool(id={self.id}, tool_name={self.tool_name}, group_id={self.group_id})>"


class MCPCallLog(BaseModel):
    """MCP调用日志数据库模型"""
    __tablename__ = "mcp_call_logs"
    __table_args__ = (
        Index('idx_mcp_logs_tool_success_time', 'tool_name', 'success', 'created_at'),
        Index('idx_mcp_logs_group_time', 'group_id', 'created_at'),
        Index('idx_mcp_logs_caller_time', 'caller_app_id', 'created_at'),
        Index('idx_mcp_logs_success', 'success'),
        Index('idx_mcp_logs_duration', 'duration_ms'),
        {"comment": "MCP调用日志表，记录工具调用历史和性能数据"}
    )

    id = Column(String(36), primary_key=True, index=True, comment="日志ID")
    tool_name = Column(String(100), nullable=False, index=True, comment="工具名称")
    group_id = Column(String(36), ForeignKey("mcp_tool_groups.id", ondelete="CASCADE"), nullable=False, index=True, comment="分组ID")
    caller_app_id = Column(String(100), nullable=True, index=True, comment="调用方应用ID（如Dify AppID）")
    request_data = Column(JSON, nullable=True, comment="请求数据")
    response_data = Column(JSON, nullable=True, comment="响应数据")
    success = Column(Boolean, nullable=False, index=True, comment="是否成功")
    error_message = Column(Text, nullable=True, comment="错误信息")
    duration_ms = Column(Integer, nullable=True, comment="执行时长（毫秒）")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True, comment="调用时间")

    # 关联关系
    group = relationship("MCPToolGroup")

    def __repr__(self):
        return f"<MCPCallLog(id={self.id}, tool={self.tool_name}, success={self.success})>"

    @property
    def response_time_category(self) -> str:
        """响应时间分类"""
        if not self.duration_ms:
            return "unknown"
        if self.duration_ms < 100:
            return "fast"
        elif self.duration_ms < 500:
            return "normal"
        elif self.duration_ms < 2000:
            return "slow"
        else:
            return "very_slow"

