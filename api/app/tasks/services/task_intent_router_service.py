import json
import logging
import re
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.ai.adapters.dify_agent_client import DifyAgentClientFactory
from app.ai.models.agent_config import AgentConfig as AgentConfigModel

logger = logging.getLogger(__name__)


class TaskIntentRouterService:
    """
    Copilot 意图路由器：
    - 输入：一段聊天文本
    - 输出：自动识别的 scene_key（可选）与 intent（可选）
    """

    ROUTER_APP_NAME = "任务意图路由器"

    def __init__(self, db: Session):
        self.db = db

    def _extract_json_obj(self, text: str) -> Optional[dict[str, Any]]:
        if not text:
            return None
        try:
            obj = json.loads(text)
            return obj if isinstance(obj, dict) else None
        except Exception:
            pass

        # 尝试提取首个 {...} JSON 对象
        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return None
        try:
            obj = json.loads(m.group(0))
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    def _get_router_agent_config(self) -> Optional[AgentConfigModel]:
        # 按 app_name 精确匹配查询
        config = (
            self.db.query(AgentConfigModel)
            .filter(
                AgentConfigModel.enabled.is_(True),
                AgentConfigModel.app_name == self.ROUTER_APP_NAME
            )
            .order_by(AgentConfigModel.created_at.desc())
            .first()
        )
        return config

    async def route_scene(
        self,
        *,
        text: str,
        user_id: str,
        candidate_scenes: list[str],
    ) -> tuple[Optional[str], Optional[str], Optional[float]]:
        """
        Returns:
            (scene_key, intent, confidence)
        """
        if not text.strip():
            return (None, None, None)
        if not candidate_scenes:
            return (None, None, None)

        config = self._get_router_agent_config()
        if not config:
            logger.info("TaskIntentRouter: 未配置 router AgentConfig，跳过 LLM 路由")
            return (None, None, None)

        prompt = (
            "你是企业聊天副驾驶的“意图路由器”。\n"
            "请根据用户文本的语义，从候选场景中选择最匹配的 scene_key。\n"
            "要求：只输出 JSON，不要输出其它任何内容。\n"
            "输出格式：\n"
            '{ "scene_key": string|null, "intent": string|null, "confidence": number|null }\n'
            "规则：\n"
            "- 如果无法判断或不属于任何候选场景，scene_key=null。\n"
            "- scene_key 必须严格等于候选列表中的一个值。\n"
            "\n"
            f"候选 scene_key 列表：{candidate_scenes}\n"
            f"用户文本：{text.strip()}\n"
        )

        try:
            dify_client = DifyAgentClientFactory.create_client(config)
            user_identifier = f"user_{user_id}"

            answer_text: Optional[str] = None
            async for chunk in dify_client.create_chat_message(
                query=prompt,
                user=user_identifier,
                conversation_id=None,
                inputs=None,
                response_mode="blocking",
            ):
                chunk_str = chunk.decode("utf-8") if isinstance(chunk, (bytes, bytearray)) else str(chunk)
                try:
                    resp = json.loads(chunk_str)
                    answer_text = resp.get("answer")
                except Exception:
                    # blocking 模式应是一整段 JSON；解析失败则作为纯文本兜底
                    answer_text = chunk_str
                break

            if not answer_text:
                return (None, None, None)

            obj = self._extract_json_obj(answer_text)
            if not obj:
                return (None, None, None)

            scene_key = obj.get("scene_key")
            intent = obj.get("intent")
            confidence = obj.get("confidence")

            if isinstance(scene_key, str):
                scene_key = scene_key.strip()
            else:
                scene_key = None

            if scene_key and scene_key not in candidate_scenes:
                scene_key = None

            if isinstance(intent, str):
                intent = intent.strip() or None
            else:
                intent = None

            if isinstance(confidence, (int, float)):
                confidence = float(confidence)
            else:
                confidence = None

            return (scene_key, intent, confidence)

        except Exception as e:
            logger.warning(f"TaskIntentRouter: LLM 路由失败，已降级: {e}", exc_info=True)
            return (None, None, None)


