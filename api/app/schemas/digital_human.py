"""
数字人相关的Pydantic模型
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DigitalHumanBase(BaseModel):
    """数字人基础模型"""
    name: str = Field(..., min_length=2, max_length=255, description="数字人名称")
    avatar: Optional[str] = Field(None, description="数字人头像URL")
    description: Optional[str] = Field(None, max_length=500, description="数字人描述")
    type: str = Field("personal", description="数字人类型")
    status: str = Field("active", description="数字人状态")
    personality: Optional[Dict[str, Any]] = Field(None, description="性格特征配置")
    greeting_message: Optional[str] = Field(None, max_length=500, description="默认打招呼消息")
    welcome_message: Optional[str] = Field(None, max_length=500, description="欢迎消息模板")


class CreateDigitalHumanRequest(DigitalHumanBase):
    """创建数字人请求"""
    pass


class UpdateDigitalHumanRequest(BaseModel):
    """更新数字人请求"""
    name: Optional[str] = Field(None, min_length=2, max_length=255, description="数字人名称")
    avatar: Optional[str] = Field(None, description="数字人头像URL")
    description: Optional[str] = Field(None, max_length=500, description="数字人描述")
    status: Optional[str] = Field(None, description="数字人状态")
    personality: Optional[Dict[str, Any]] = Field(None, description="性格特征配置")
    greeting_message: Optional[str] = Field(None, max_length=500, description="默认打招呼消息")
    welcome_message: Optional[str] = Field(None, max_length=500, description="欢迎消息模板")


class UserInfo(BaseModel):
    """用户信息"""
    id: str
    username: str
    email: str
    phone: Optional[str] = None


class AgentConfigInfo(BaseModel):
    """智能体配置信息"""
    id: str
    app_name: str
    app_id: str
    environment: str
    description: Optional[str] = None
    enabled: bool
    agent_type: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None


class DigitalHumanAgentConfigInfo(BaseModel):
    """数字人智能体配置信息"""
    id: str
    priority: int
    is_active: bool
    scenarios: Optional[List[str]] = None
    context_prompt: Optional[str] = None
    agent_config: AgentConfigInfo


class DigitalHumanResponse(DigitalHumanBase):
    """数字人响应模型"""
    id: str
    isSystemCreated: bool = Field(alias="is_system_created")
    userId: str = Field(alias="user_id")
    conversationCount: int = Field(alias="conversation_count")
    messageCount: int = Field(alias="message_count")
    lastActiveAt: Optional[datetime] = Field(None, alias="last_active_at")
    createdAt: datetime = Field(alias="created_at")
    updatedAt: datetime = Field(alias="updated_at")
    
    # 关联信息
    user: Optional[UserInfo] = None
    agentConfigs: Optional[List[DigitalHumanAgentConfigInfo]] = Field(None, alias="agent_configs")
    agentCount: Optional[int] = Field(None, alias="agent_count")
    
    class Config:
        populate_by_name = True

    @staticmethod
    def from_model(digital_human) -> "DigitalHumanResponse":
        """从数字人模型转换为响应模型"""
        return DigitalHumanResponse(
            id=digital_human.id,
            name=digital_human.name,
            avatar=digital_human.avatar,
            description=digital_human.description,
            type=digital_human.type,
            status=digital_human.status,
            isSystemCreated=digital_human.is_system_created,
            personality=digital_human.personality,
            greeting_message=digital_human.greeting_message,
            welcome_message=digital_human.welcome_message,
            userId=digital_human.user_id,
            conversationCount=digital_human.conversation_count,
            messageCount=digital_human.message_count,
            lastActiveAt=digital_human.last_active_at,
            createdAt=digital_human.created_at,
            updatedAt=digital_human.updated_at,
            user=UserInfo(
                id=digital_human.user.id,
                username=digital_human.user.username,
                email=digital_human.user.email,
                phone=digital_human.user.phone
            ) if digital_human.user else None,
            agentConfigs=[
                DigitalHumanAgentConfigInfo(
                    id=config.id,
                    priority=config.priority,
                    is_active=config.is_active,
                    scenarios=config.scenarios,
                    context_prompt=config.context_prompt,
                    agent_config=AgentConfigInfo(
                        id=config.agent_config.id,
                        app_name=config.agent_config.app_name,
                        app_id=config.agent_config.app_id,
                        environment=config.agent_config.environment,
                        description=config.agent_config.description,
                        enabled=config.agent_config.enabled,
                        agent_type=config.agent_config.agent_type,
                        capabilities=config.agent_config.capabilities
                    )
                ) for config in digital_human.agent_configs
            ] if hasattr(digital_human, 'agent_configs') and digital_human.agent_configs else [],
            agentCount=len(digital_human.agent_configs) if hasattr(digital_human, 'agent_configs') and digital_human.agent_configs else 0
        )


class AddAgentConfigRequest(BaseModel):
    """为数字人添加智能体配置请求"""
    agent_config_id: str = Field(..., description="智能体配置ID")
    priority: int = Field(1, ge=1, description="优先级（数字越小优先级越高）")
    scenarios: Optional[List[str]] = Field(None, description="适用场景")
    context_prompt: Optional[str] = Field(None, max_length=1000, description="上下文提示词")
    is_active: bool = Field(True, description="是否启用")


class UpdateAgentConfigRequest(BaseModel):
    """更新数字人智能体配置请求"""
    priority: Optional[int] = Field(None, ge=1, description="优先级")
    scenarios: Optional[List[str]] = Field(None, description="适用场景")
    context_prompt: Optional[str] = Field(None, max_length=1000, description="上下文提示词")
    is_active: Optional[bool] = Field(None, description="是否启用")


class AdminDigitalHumanResponse(DigitalHumanResponse):
    """管理员端数字人响应模型（包含更多信息）"""
    pass


class UpdateDigitalHumanStatusRequest(BaseModel):
    """更新数字人状态请求"""
    status: str = Field(..., description="新状态：active, inactive, maintenance")
