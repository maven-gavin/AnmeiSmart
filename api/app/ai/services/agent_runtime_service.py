"""Agent 运行时统一编排服务。"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional

from openai import AsyncOpenAI
from sqlalchemy.orm import Session

from app.ai.models.agent_config import AgentConfig
from app.ai.models.agent_message import AgentMessage
from app.ai.runtime.agent_runner import AgentRunner
from app.ai.runtime.capabilities import AgentCapabilities
from app.ai.runtime.structured_runner import StructuredLLMRunner
from app.ai.runtime.task_registry import AgentTaskRegistry
from app.ai.services.conversation_service import ConversationService
from app.common.deps.uuid_utils import generate_agent_message_id
from app.common.services.file_service import FileService

logger = logging.getLogger(__name__)


class AgentRuntimeService:
    """LangGraph/LangChain Agent 运行时入口。"""

    def __init__(self, db: Session):
        self.db = db
        self.conversations = ConversationService(db)
        self.runner = AgentRunner(db)
        self.structured = StructuredLLMRunner(db)

    def _load_agent_config(self, agent_config_id: str) -> AgentConfig:
        config = (
            self.db.query(AgentConfig)
            .filter(AgentConfig.id == agent_config_id, AgentConfig.enabled.is_(True))
            .first()
        )
        if not config:
            raise ValueError(f"Agent 配置不存在或未启用: {agent_config_id}")
        if not config.api_key:
            raise ValueError(f"Agent 配置缺少 API Key: {agent_config_id}")
        return config

    def _capabilities(self, config: AgentConfig) -> AgentCapabilities:
        return AgentCapabilities.from_agent_config(config.app_name, config.capabilities)

    async def stream_chat(
        self,
        *,
        agent_config_id: str,
        user_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        inputs: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[bytes]:
        config = self._load_agent_config(agent_config_id)
        capabilities = self._capabilities(config)

        conv = self.conversations.get_or_create_conversation(
            agent_config_id=agent_config_id,
            user_id=user_id,
            conversation_id=conversation_id,
        )

        self.conversations.add_message(
            conversation_id=conv.id,
            role="user",
            content=message,
            metadata={"inputs": inputs or {}},
        )

        history = self.conversations.get_recent_langchain_history(conv.id, limit=20)
        # 排除刚写入的用户消息（runner 会再次 append）
        history = [m for m in history if not (m.role == "user" and m.content == message)][-19:]

        assistant_message_id = generate_agent_message_id()
        full_answer_parts: list[str] = []

        async for chunk in self.runner.stream_chat(
            agent_config=config,
            capabilities=capabilities,
            history=history,
            query=message,
            conversation_id=conv.id,
            message_id=assistant_message_id,
            inputs=inputs,
        ):
            chunk_str = chunk.decode("utf-8")
            if '"event": "message"' in chunk_str or '"event": "agent_message"' in chunk_str:
                try:
                    data_line = chunk_str.split("data: ", 1)[1].strip()
                    payload = json.loads(data_line.split("\n")[0])
                    if payload.get("answer"):
                        full_answer_parts.append(payload["answer"])
                except Exception:
                    pass
            yield chunk

        answer_text = "".join(full_answer_parts)
        if answer_text:
            self.conversations.add_message(
                conversation_id=conv.id,
                role="assistant",
                content=answer_text,
                message_id=assistant_message_id,
                metadata={"task_id": None},
            )

    async def invoke_by_app_name(self, app_name: str, prompt: str) -> Optional[str]:
        config = StructuredLLMRunner.load_config_by_app_name(self.db, app_name)
        if not config:
            return None
        caps = self._capabilities(config)
        return await self.structured.invoke_text(config, caps, prompt)

    async def get_application_parameters(self, agent_config_id: str) -> Dict[str, Any]:
        config = self._load_agent_config(agent_config_id)
        return self._capabilities(config).to_application_parameters()

    def get_application_meta(self, agent_config_id: str) -> Dict[str, Any]:
        self._load_agent_config(agent_config_id)
        return {"tool_icons": {}}

    async def upload_file(self, agent_config_id: str, file: Any, user_id: str) -> Dict[str, Any]:
        config = self._load_agent_config(agent_config_id)
        caps = self._capabilities(config)
        if not caps.file_upload_enabled:
            raise ValueError("该 Agent 未启用文件上传")

        import mimetypes
        import os
        import uuid as uuid_lib

        filename, content, mime_type = file["file"]
        if not mime_type:
            mime_type, _ = mimetypes.guess_type(filename)
            mime_type = mime_type or "application/octet-stream"

        file_service = FileService(self.db)
        ext = os.path.splitext(filename)[1]
        object_name = f"{user_id}/agent/{agent_config_id}/{uuid_lib.uuid4().hex}{ext}"
        file_service.minio_client.upload_file_data(
            object_name=object_name,
            file_data=content,
            content_type=mime_type,
        )
        file_id = file_service.create_file_record(
            object_name=object_name,
            file_name=filename,
            file_size=len(content),
            mime_type=mime_type,
            file_type=file_service.get_file_category(mime_type),
            user_id=user_id,
            business_type="agent_document",
            business_id=agent_config_id,
            db=self.db,
        )
        return {
            "id": file_id,
            "name": filename,
            "size": len(content),
            "mime_type": mime_type,
            "created_at": int(__import__("time").time()),
        }

    async def get_suggested_questions(
        self,
        agent_config_id: str,
        message_id: str,
        user_id: str,
    ) -> List[str]:
        config = self._load_agent_config(agent_config_id)
        caps = self._capabilities(config)
        if not caps.suggested_questions_after_answer:
            return []

        msg = self.db.query(AgentMessage).filter(AgentMessage.id == message_id).first()
        if not msg or not msg.content:
            return []

        prompt = (
            "根据以下 AI 回复，生成 3 个用户可能继续追问的简短问题。"
            "只输出 JSON 数组，例如 [\"问题1\",\"问题2\",\"问题3\"]，不要其它内容。\n\n"
            f"AI 回复：{msg.content[:2000]}"
        )
        raw = await self.structured.invoke_text(config, caps, prompt)
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                return [str(x) for x in data[:3]]
        except Exception:
            pass
        return []

    def stop_message_generation(self, task_id: str) -> Dict[str, Any]:
        ok = AgentTaskRegistry.cancel(task_id)
        return {"result": "success" if ok else "not_found"}

    async def audio_to_text(self, agent_config_id: str, audio_file: Any, user_id: str) -> str:
        config = self._load_agent_config(agent_config_id)
        client = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url or None)
        filename, content, _mime = audio_file["file"]
        response = await client.audio.transcriptions.create(
            model="whisper-1",
            file=(filename, content),
        )
        return response.text or ""

    async def text_to_audio(
        self,
        agent_config_id: str,
        text: str,
        user_id: str,
        streaming: bool = False,
    ) -> Dict[str, Any]:
        config = self._load_agent_config(agent_config_id)
        client = AsyncOpenAI(api_key=config.api_key, base_url=config.base_url or None)
        response = await client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
        )
        audio_bytes = response.read()
        return {"audio": audio_bytes, "streaming": streaming}

    def message_feedback(self, message_id: str, user_id: str, rating: str) -> Dict[str, Any]:
        return self.conversations.save_feedback(message_id=message_id, user_id=user_id, rating=rating)

    async def test_llm_connection(self, config: AgentConfig) -> Dict[str, Any]:
        """测试 LLM API 连通性。"""
        caps = self._capabilities(config)
        try:
            text = await self.structured.invoke_text(config, caps, "Reply with OK only.")
            return {
                "success": True,
                "message": "LLM 连接测试成功",
                "details": {
                    "model": caps.model,
                    "base_url": config.base_url,
                    "sample": (text or "")[:100],
                },
            }
        except Exception as exc:
            return {
                "success": False,
                "message": f"LLM 连接测试失败: {exc}",
                "details": {"model": caps.model, "base_url": config.base_url, "error": str(exc)},
            }
