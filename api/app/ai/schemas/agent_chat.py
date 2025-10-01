"""
Agent 对话 Schema 定义
定义 API 请求和响应的数据结构
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class AgentChatRequest(BaseModel):
    """Agent 对话请求"""
    message: str = Field(..., description="用户消息", min_length=1)
    conversation_id: Optional[str] = Field(None, description="会话ID，为空则创建新会话")
    response_mode: str = Field("streaming", description="响应模式：streaming/blocking")
    inputs: Dict[str, Any] = Field(default_factory=dict, description="额外输入参数")


class AgentConversationCreate(BaseModel):
    """创建会话请求"""
    title: Optional[str] = Field(None, description="会话标题")


class AgentConversationUpdate(BaseModel):
    """更新会话请求"""
    title: str = Field(..., description="会话标题")


class AgentMessageResponse(BaseModel):
    """消息响应"""
    id: str
    conversation_id: str
    content: str
    is_answer: bool
    timestamp: str
    agent_thoughts: Optional[List[Dict[str, Any]]] = None
    files: Optional[List[Dict[str, Any]]] = None
    is_error: Optional[bool] = None


class AgentConversationResponse(BaseModel):
    """会话响应"""
    id: str
    agent_config_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    last_message: Optional[str] = None


class AgentThoughtData(BaseModel):
    """Agent 思考数据"""
    id: str
    thought: str
    tool: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Any] = None
    observation: Optional[str] = None
    position: int

