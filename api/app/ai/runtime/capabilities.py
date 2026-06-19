"""Agent 运行时能力配置解析。"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.core.config import get_settings

settings = get_settings()

# 内置 Agent 预设（开发阶段可在后台 capabilities 覆盖）
BUILTIN_AGENT_PRESETS: dict[str, dict[str, Any]] = {
    "任务意图路由器": {
        "model": settings.AGENT_DEFAULT_MODEL,
        "system_prompt": (
            "你是企业聊天副驾驶的「意图路由器」。"
            "根据用户文本从候选场景中选择最匹配的 scene_key。"
            "必须只输出 JSON，不要输出任何解释、markdown 或代码块。"
        ),
        "temperature": 0.1,
        "response_mode": "blocking",
        "enable_tools": False,
        "enable_rag": False,
    },
    "客户画像洞察器": {
        "model": settings.AGENT_DEFAULT_MODEL,
        "system_prompt": "你是客户画像洞察器，只输出 JSON，不要输出其他文字。",
        "temperature": 0.2,
        "response_mode": "blocking",
        "enable_tools": False,
        "enable_rag": False,
    },
}


class InputFormField(BaseModel):
    """对话前输入表单字段。"""

    type: str
    variable: str
    label: str
    required: bool = False
    default: Optional[Any] = None
    options: List[str] = Field(default_factory=list)


class AgentCapabilities(BaseModel):
    """Agent 运行时能力定义，存储于 agent_configs.capabilities。"""

    model: str = Field(default_factory=lambda: settings.AGENT_DEFAULT_MODEL)
    embedding_model: str = Field(default_factory=lambda: settings.AGENT_DEFAULT_EMBEDDING_MODEL)
    system_prompt: str = ""
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    response_mode: str = "streaming"  # streaming | blocking
    enable_tools: bool = True
    enable_rag: bool = False
    knowledge_base_id: Optional[str] = None
    mcp_tool_groups: List[str] = Field(default_factory=list)
    input_form: List[InputFormField] = Field(default_factory=list)
    opening_statement: Optional[str] = None
    suggested_questions: List[str] = Field(default_factory=list)
    suggested_questions_after_answer: bool = False
    file_upload_enabled: bool = True
    speech_to_text_enabled: bool = False
    text_to_speech_enabled: bool = False
    retriever_resource_enabled: bool = False

    @classmethod
    def from_agent_config(cls, app_name: str, raw: Optional[Dict[str, Any]]) -> "AgentCapabilities":
        merged: Dict[str, Any] = {}
        preset = BUILTIN_AGENT_PRESETS.get(app_name or "")
        if preset:
            merged.update(preset)
        if raw:
            merged.update(raw)

        input_form_raw = merged.pop("input_form", []) or []
        input_form: List[InputFormField] = []
        for item in input_form_raw:
            if isinstance(item, dict):
                input_form.append(InputFormField.model_validate(item))

        caps = cls.model_validate({**merged, "input_form": input_form or []})
        return caps

    def to_application_parameters(self) -> Dict[str, Any]:
        """转换为前端兼容的应用参数结构。"""
        return {
            "user_input_form": [field.model_dump() for field in self.input_form],
            "file_upload": {
                "enabled": self.file_upload_enabled,
                "allowed_file_types": ["document", "image"],
                "allowed_file_extensions": [".pdf", ".txt", ".md", ".docx", ".png", ".jpg", ".jpeg"],
                "allowed_file_upload_methods": ["local_file"],
                "number_limits": 5,
            },
            "system_parameters": {
                "model": self.model,
                "temperature": self.temperature,
            },
            "opening_statement": self.opening_statement,
            "suggested_questions": self.suggested_questions,
            "suggested_questions_after_answer": {
                "enabled": self.suggested_questions_after_answer,
            },
            "speech_to_text": {"enabled": self.speech_to_text_enabled},
            "text_to_speech": {"enabled": self.text_to_speech_enabled},
            "retriever_resource": {"enabled": self.retriever_resource_enabled or self.enable_rag},
            "annotation_reply": {"enabled": False},
            "more_like_this": {"enabled": False},
            "sensitive_word_avoidance": {"enabled": False},
        }
