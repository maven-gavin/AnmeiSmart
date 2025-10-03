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


# ========== 消息反馈相关 ==========

class MessageFeedbackRequest(BaseModel):
    """消息反馈请求"""
    message_id: str = Field(..., description="消息ID")
    rating: str = Field(..., description="评分：like 或 dislike")


class MessageFeedbackResponse(BaseModel):
    """消息反馈响应"""
    success: bool
    message: str


# ========== 建议问题相关 ==========

class SuggestedQuestionsResponse(BaseModel):
    """建议问题响应"""
    questions: List[str] = Field(default_factory=list, description="建议的问题列表")


# ========== 停止生成相关 ==========

class StopMessageRequest(BaseModel):
    """停止消息生成请求"""
    task_id: str = Field(..., description="任务ID")


class StopMessageResponse(BaseModel):
    """停止消息生成响应"""
    success: bool
    message: str


# ========== 媒体处理相关 ==========

class AudioToTextRequest(BaseModel):
    """语音转文字请求"""
    pass  # 文件通过 UploadFile 上传


class AudioToTextResponse(BaseModel):
    """语音转文字响应"""
    text: str = Field(..., description="转换后的文本")


class TextToAudioRequest(BaseModel):
    """文字转语音请求"""
    text: str = Field(..., description="要转换的文本", min_length=1)
    streaming: bool = Field(False, description="是否流式返回")


class FileUploadRequest(BaseModel):
    """文件上传请求"""
    pass  # 文件通过 UploadFile 上传


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    id: str = Field(..., description="上传文件ID")
    name: str = Field(..., description="文件名")
    size: int = Field(..., description="文件大小（字节）")
    mime_type: str = Field(..., description="文件类型")
    created_at: str = Field(..., description="创建时间")


# ========== 应用配置相关 ==========

class ApplicationParametersResponse(BaseModel):
    """应用参数响应"""
    user_input_form: List[Dict[str, Any]] = Field(default_factory=list, description="用户输入表单配置")
    file_upload: Optional[Dict[str, Any]] = Field(None, description="文件上传配置")
    system_parameters: Optional[Dict[str, Any]] = Field(None, description="系统参数")
    opening_statement: Optional[str] = Field(None, description="开场白")
    suggested_questions: List[str] = Field(default_factory=list, description="建议问题")
    suggested_questions_after_answer: Optional[Dict[str, Any]] = Field(None, description="回答后的建议问题配置")
    speech_to_text: Optional[Dict[str, Any]] = Field(None, description="语音转文字配置")
    text_to_speech: Optional[Dict[str, Any]] = Field(None, description="文字转语音配置")
    retriever_resource: Optional[Dict[str, Any]] = Field(None, description="检索资源配置")
    annotation_reply: Optional[Dict[str, Any]] = Field(None, description="注释回复配置")
    more_like_this: Optional[Dict[str, Any]] = Field(None, description="更多类似内容配置")
    sensitive_word_avoidance: Optional[Dict[str, Any]] = Field(None, description="敏感词规避配置")


class ApplicationMetaResponse(BaseModel):
    """应用元数据响应"""
    tool_icons: Dict[str, Any] = Field(default_factory=dict, description="工具图标")

