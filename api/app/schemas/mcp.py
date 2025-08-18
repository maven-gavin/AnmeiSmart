from pydantic import BaseModel, Field, field_validator, field_serializer    
from typing import Optional, List, Dict, Any
from datetime import datetime

# =============== MCP分组相关Schema ===============

class MCPGroupBase(BaseModel):
    """MCP分组基础模型"""
    name: str = Field(..., description="分组名称", max_length=100, min_length=1)
    description: Optional[str] = Field(None, description="分组描述", max_length=255)
    user_tier_access: List[str] = Field(default=["internal"], description="允许访问的用户层级")
    allowed_roles: List[str] = Field(default=[], description="允许访问的角色列表")
    enabled: bool = Field(True, description="是否启用")

    @field_validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('分组名称不能为空')
        return v.strip()

    @field_validator('user_tier_access')
    def validate_user_tier_access(cls, v):
        valid_tiers = ["internal", "external", "public", "premium"]
        for tier in v:
            if tier not in valid_tiers:
                raise ValueError(f'无效的用户层级: {tier}')
        return v

class MCPGroupCreate(MCPGroupBase):
    """创建MCP分组的请求模型"""
    pass

class MCPGroupUpdate(BaseModel):
    """更新MCP分组的请求模型"""
    name: Optional[str] = Field(None, description="分组名称", max_length=100, min_length=1)
    description: Optional[str] = Field(None, description="分组描述", max_length=255)
    user_tier_access: Optional[List[str]] = Field(None, description="允许访问的用户层级")
    allowed_roles: Optional[List[str]] = Field(None, description="允许访问的角色列表")
    enabled: Optional[bool] = Field(None, description="是否启用")

    @field_validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('分组名称不能为空')
        return v.strip() if v else v

class MCPGroupInfo(MCPGroupBase):
    """MCP分组完整信息模型"""
    id: str = Field(..., description="分组ID")
    api_key_preview: str = Field(..., description="API密钥预览（脱敏）")
    server_code: Optional[str] = Field(None, description="MCP服务器代码（用于URL路径）")
    tools_count: int = Field(0, description="工具数量")
    created_by: str = Field(..., description="创建者ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True

    @staticmethod
    def from_model(group_model) -> "MCPGroupInfo":
        """从ORM模型转换为Schema"""
        # API密钥脱敏处理
        api_key_preview = ""
        if hasattr(group_model, 'api_key') and group_model.api_key:
            api_key_preview = f"{group_model.api_key[:12]}***{group_model.api_key[-4:]}"
        
        return MCPGroupInfo(
            id=group_model.id,
            name=group_model.name,
            description=group_model.description,
            api_key_preview=api_key_preview,
            server_code=group_model.server_code,
            user_tier_access=group_model.user_tier_access or ["internal"],
            allowed_roles=group_model.allowed_roles or [],
            enabled=group_model.enabled,
            tools_count=len(group_model.tools) if hasattr(group_model, 'tools') and group_model.tools else 0,
            created_by=group_model.created_by,
            created_at=group_model.created_at,
            updated_at=group_model.updated_at
        )

# =============== MCP工具相关Schema ===============

class MCPToolBase(BaseModel):
    """MCP工具基础模型"""
    tool_name: str = Field(..., description="工具名称", max_length=100, min_length=1)
    description: Optional[str] = Field(None, description="工具描述", max_length=255)
    enabled: bool = Field(True, description="是否启用")
    timeout_seconds: int = Field(30, description="超时时间（秒）", ge=1, le=300)
    config_data: Dict[str, Any] = Field(default_factory=dict, description="工具配置数据")

    @field_validator('tool_name')
    def validate_tool_name(cls, v):
        if not v.strip():
            raise ValueError('工具名称不能为空')
        return v.strip()

class MCPToolCreate(MCPToolBase):
    """创建MCP工具的请求模型"""
    group_id: str = Field(..., description="所属分组ID")
    version: str = Field("1.0.0", description="工具版本", max_length=20)

class MCPToolUpdate(BaseModel):
    """更新MCP工具的请求模型"""
    group_id: Optional[str] = Field(None, description="所属分组ID")
    description: Optional[str] = Field(None, description="工具描述", max_length=255)
    enabled: Optional[bool] = Field(None, description="是否启用")
    timeout_seconds: Optional[int] = Field(None, description="超时时间（秒）", ge=1, le=300)
    config_data: Optional[Dict[str, Any]] = Field(None, description="工具配置数据")

class MCPToolInfo(MCPToolBase):
    """MCP工具完整信息模型"""
    id: str = Field(..., description="工具ID")
    group_id: str = Field(..., description="所属分组ID")
    group_name: Optional[str] = Field(None, description="分组名称")
    version: str = Field(..., description="工具版本")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    class Config:
        from_attributes = True

    @staticmethod
    def from_model(tool_model) -> "MCPToolInfo":
        """从ORM模型转换为Schema"""
        return MCPToolInfo(
            id=tool_model.id,
            group_id=tool_model.group_id,
            group_name=tool_model.group.name if hasattr(tool_model, 'group') and tool_model.group else None,
            tool_name=tool_model.tool_name,
            description=tool_model.description,
            enabled=tool_model.enabled,
            timeout_seconds=tool_model.timeout_seconds,
            config_data=tool_model.config_data or {},
            version=tool_model.version or "1.0.0",
            created_at=tool_model.created_at,
            updated_at=tool_model.updated_at
        )

# =============== MCP调用日志相关Schema ===============

class MCPCallLogBase(BaseModel):
    """MCP调用日志基础模型"""
    tool_name: str = Field(..., description="工具名称")
    group_id: str = Field(..., description="分组ID")
    caller_app_id: Optional[str] = Field(None, description="调用方应用ID")
    request_data: Dict[str, Any] = Field(default_factory=dict, description="请求数据")
    response_data: Dict[str, Any] = Field(default_factory=dict, description="响应数据")
    success: bool = Field(..., description="是否成功")
    error_message: Optional[str] = Field(None, description="错误信息")
    duration_ms: Optional[int] = Field(None, description="执行时长（毫秒）", ge=0)

class MCPCallLogInfo(MCPCallLogBase):
    """MCP调用日志完整信息模型"""
    id: str = Field(..., description="日志ID")
    created_at: datetime = Field(..., description="调用时间")

    class Config:
        from_attributes = True

    @staticmethod
    def from_model(log_model) -> "MCPCallLogInfo":
        """从ORM模型转换为Schema"""
        return MCPCallLogInfo(
            id=log_model.id,
            tool_name=log_model.tool_name,
            group_id=log_model.group_id,
            caller_app_id=log_model.caller_app_id,
            request_data=log_model.request_data or {},
            response_data=log_model.response_data or {},
            success=log_model.success,
            error_message=log_model.error_message,
            duration_ms=log_model.duration_ms,
            created_at=log_model.created_at
        )

# =============== API响应模型 ===============

class MCPBaseResponse(BaseModel):
    """MCP基础响应模型"""
    success: bool = Field(True, description="是否成功")
    message: str = Field("操作成功", description="响应消息")

class MCPGroupListResponse(MCPBaseResponse):
    """MCP分组列表响应模型"""
    data: List[MCPGroupInfo] = Field(..., description="分组列表")

class MCPGroupSingleResponse(MCPBaseResponse):
    """MCP分组单个响应模型"""
    data: MCPGroupInfo = Field(..., description="分组信息")

class MCPToolListResponse(MCPBaseResponse):
    """MCP工具列表响应模型"""
    data: List[MCPToolInfo] = Field(..., description="工具列表")

class MCPToolSingleResponse(MCPBaseResponse):
    """MCP工具单个响应模型"""
    data: MCPToolInfo = Field(..., description="工具信息")

class MCPApiKeyResponse(MCPBaseResponse):
    """API密钥响应模型"""
    data: Dict[str, str] = Field(..., description="API密钥数据")

class MCPServerUrlResponse(MCPBaseResponse):
    """MCP服务器URL响应模型"""
    data: Dict[str, str] = Field(..., description="MCP服务器URL数据")

class MCPSuccessResponse(MCPBaseResponse):
    """成功响应模型"""
    pass

class MCPErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="是否成功")
    error: str = Field(..., description="错误信息")
    error_code: Optional[str] = Field(None, description="错误代码")

# =============== MCP服务器状态相关Schema ===============

class MCPServerStatusResponse(MCPBaseResponse):
    """MCP服务器状态响应模型"""
    data: Dict[str, Any] = Field(..., description="服务器状态数据")

class MCPServerMetrics(BaseModel):
    """MCP服务器指标模型"""
    total_calls: int = Field(0, description="总调用次数", ge=0)
    success_calls: int = Field(0, description="成功调用次数", ge=0)
    failed_calls: int = Field(0, description="失败调用次数", ge=0)
    average_response_time: float = Field(0.0, description="平均响应时间（毫秒）", ge=0)
    uptime_seconds: int = Field(0, description="运行时间（秒）", ge=0)
    active_groups: int = Field(0, description="活跃分组数", ge=0)
    active_tools: int = Field(0, description="活跃工具数", ge=0)

    @staticmethod
    def from_raw_data(data: Dict[str, Any]) -> "MCPServerMetrics":
        """从原始数据转换为指标模型"""
        return MCPServerMetrics(
            total_calls=data.get("total_calls", 0),
            success_calls=data.get("success_calls", 0),
            failed_calls=data.get("failed_calls", 0),
            average_response_time=data.get("average_response_time", 0.0),
            uptime_seconds=data.get("uptime_seconds", 0),
            active_groups=data.get("active_groups", 0),
            active_tools=data.get("active_tools", 0)
        ) 