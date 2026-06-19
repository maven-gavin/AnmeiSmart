import json
import logging
import re
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.ai.services.agent_runtime_service import AgentRuntimeService

logger = logging.getLogger(__name__)


class TaskIntentRouterService:
    """Copilot 意图路由器（LangChain blocking）。"""

    ROUTER_APP_NAME = "任务意图路由器"

    def __init__(self, db: Session):
        self.db = db
        self.runtime = AgentRuntimeService(db)

    def _extract_json_obj(self, text: str) -> Optional[dict[str, Any]]:
        if not text:
            return None
        try:
            obj = json.loads(text)
            return obj if isinstance(obj, dict) else None
        except Exception:
            pass

        m = re.search(r"\{[\s\S]*\}", text)
        if not m:
            return None
        try:
            obj = json.loads(m.group(0))
            return obj if isinstance(obj, dict) else None
        except Exception:
            return None

    async def route_scene(
        self,
        *,
        text: str,
        user_id: str,
        candidate_scenes: list[str],
    ) -> tuple[Optional[str], Optional[str], Optional[float]]:
        if not text.strip() or not candidate_scenes:
            return (None, None, None)

        prompt = (
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
            answer_text = await self.runtime.invoke_by_app_name(self.ROUTER_APP_NAME, prompt)
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
            logger.warning("TaskIntentRouter: LLM 路由失败，已降级: %s", e, exc_info=True)
            return (None, None, None)
