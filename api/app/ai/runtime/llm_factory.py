"""LLM 实例工厂。"""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.ai.models.agent_config import AgentConfig
from app.ai.runtime.capabilities import AgentCapabilities


class LLMFactory:
    """根据 AgentConfig 创建 LangChain Chat 模型。"""

    @staticmethod
    def create_chat_model(
        agent_config: AgentConfig,
        capabilities: AgentCapabilities,
        *,
        streaming: bool = False,
    ) -> ChatOpenAI:
        api_key = agent_config.api_key
        if not api_key:
            raise ValueError(f"Agent 配置缺少 API Key: {agent_config.id}")

        kwargs: dict = {
            "model": capabilities.model,
            "api_key": api_key,
            "base_url": agent_config.base_url or None,
            "temperature": capabilities.temperature,
            "timeout": agent_config.timeout_seconds,
            "max_retries": agent_config.max_retries,
            "streaming": streaming,
        }
        if capabilities.max_tokens is not None:
            kwargs["max_tokens"] = capabilities.max_tokens
        return ChatOpenAI(**kwargs)
