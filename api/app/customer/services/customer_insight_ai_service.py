"""
客户画像洞察（AI）服务

目标：
- 在“客户发送新消息”后，调用 SmartBrain(Dify) 提取洞察
- 将洞察写入 customer_insights（时间流），并可选更新 customer_profiles.ai_summary

说明：
- 该能力依赖 AgentConfig（数据库配置），通过 app_name 精确匹配启用
- 未配置时自动跳过，不影响主流程
"""

import json
import logging
import re
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.ai.adapters.dify_agent_client import DifyAgentClientFactory
from app.ai.models.agent_config import AgentConfig as AgentConfigModel
from app.chat.models.chat import Message
from app.customer.models.customer import CustomerProfile, CustomerInsight, InsightSource, InsightStatus

logger = logging.getLogger(__name__)


class CustomerInsightAIService:
    """客户画像洞察（AI）服务"""

    APP_NAME = "客户画像洞察器"

    def __init__(self, db: Session):
        self.db = db

    def _get_agent_config(self) -> Optional[AgentConfigModel]:
        config = (
            self.db.query(AgentConfigModel)
            .filter(
                AgentConfigModel.enabled.is_(True),
                AgentConfigModel.app_name == self.APP_NAME,
            )
            .order_by(AgentConfigModel.created_at.desc())
            .first()
        )
        return config

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

    def _message_to_text(self, msg: Message) -> str:
        """将消息 content 转成可用于 LLM 的文本"""
        if not msg or not msg.content:
            return ""
        if isinstance(msg.content, dict):
            if msg.content.get("type") == "text":
                return str(msg.content.get("text") or "").strip()
            # 媒体消息可能带 text
            if msg.content.get("type") == "media":
                return str(msg.content.get("text") or "").strip()
            # 结构化/系统消息：不作为客户自然语言输入
            return ""
        if isinstance(msg.content, str):
            return msg.content.strip()
        return ""

    async def analyze_and_persist_from_message(
        self,
        *,
        customer_id: str,
        conversation_id: str,
        message_id: str,
        context_messages_limit: int = 20,
        context_insights_limit: int = 30,
    ) -> None:
        """
        从“某条新消息”触发一次洞察提取并落库。
        """
        config = self._get_agent_config()
        if not config:
            logger.info("CustomerInsightAI: 未配置 AgentConfig(app_name=客户画像洞察器)，跳过洞察提取")
            return

        # 1) 获取/创建客户档案
        profile = (
            self.db.query(CustomerProfile)
            .filter(CustomerProfile.customer_id == customer_id)
            .first()
        )
        if not profile:
            profile = CustomerProfile(customer_id=customer_id)
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)

        # 2) 构造上下文：最近消息 + 既有洞察
        recent_messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.desc())
            .limit(context_messages_limit)
            .all()
        )
        recent_messages.reverse()  # 让上下文按时间正序

        message_lines: list[str] = []
        for m in recent_messages:
            text = self._message_to_text(m)
            if not text:
                continue
            # sender_id 可能为空（渠道入站），但当前阶段我们主要处理站内 customer
            sender_label = "客户" if str(m.sender_id or "") == str(customer_id) else "对方"
            message_lines.append(f"- {sender_label}: {text}")

        active_insights = (
            self.db.query(CustomerInsight)
            .filter(
                CustomerInsight.profile_id == profile.id,
                CustomerInsight.status == InsightStatus.ACTIVE.value,
            )
            .order_by(CustomerInsight.created_at.desc())
            .limit(context_insights_limit)
            .all()
        )

        insight_lines: list[str] = []
        for ins in reversed(active_insights):
            insight_lines.append(f"- [{ins.category}] {ins.content}")

        prompt = (
            "你是“智能沟通系统”的客户画像洞察器。\n"
            "输入：客户最新对话上下文 + 现有客户画像摘要/洞察。\n"
            "输出：只输出 JSON，不要输出任何其他文字。\n"
            "\n"
            "请产出：\n"
            "1) ai_summary：一句到三句客户摘要（面向销售）\n"
            "2) insights：新增洞察列表（用于时间流），每条洞察必须包含 category 和 content，可选 confidence\n"
            "\n"
            "category 只能取：need, budget, authority, timeline, preference, risk, trait, background, other\n"
            "约束：\n"
            "- 不要编造没有在对话中出现的信息。\n"
            "- 洞察要短、可行动、可复用。\n"
            "\n"
            "输出 JSON 格式：\n"
            '{ "ai_summary": string|null, "insights": [ { "category": string, "content": string, "confidence": number|null } ] }\n'
            "\n"
            f"客户ID：{customer_id}\n"
            f"现有 ai_summary：{(profile.ai_summary or '').strip()}\n"
            "现有洞察（Active）：\n"
            + ("\n".join(insight_lines) if insight_lines else "- (无)\n")
            + "\n"
            "最近对话：\n"
            + ("\n".join(message_lines) if message_lines else "- (无)\n")
        )

        # 3) 调用 Dify（blocking）
        dify_client = DifyAgentClientFactory.create_client(config)
        user_identifier = f"user_{customer_id}"

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
                answer_text = chunk_str
            break

        if not answer_text:
            return

        obj = self._extract_json_obj(answer_text)
        if not obj:
            logger.warning(f"CustomerInsightAI: 输出无法解析为JSON，已跳过: {answer_text[:200]}")
            return

        # 4) 落库：summary + insights（全部追加为时间流；覆盖策略后续单独讲清楚再增强）
        ai_summary = obj.get("ai_summary")
        if isinstance(ai_summary, str) and ai_summary.strip():
            profile.ai_summary = ai_summary.strip()

        insights = obj.get("insights") or []
        if isinstance(insights, list):
            for item in insights:
                if not isinstance(item, dict):
                    continue
                category = item.get("category")
                content = item.get("content")
                confidence = item.get("confidence")

                if not isinstance(category, str) or not category.strip():
                    continue
                if not isinstance(content, str) or not content.strip():
                    continue

                cat = category.strip()
                txt = content.strip()

                conf_val: Optional[float] = None
                if isinstance(confidence, (int, float)):
                    conf_val = float(confidence)

                # 简单去重：同类同内容的 active 已存在则不重复写入
                exists = (
                    self.db.query(CustomerInsight)
                    .filter(
                        CustomerInsight.profile_id == profile.id,
                        CustomerInsight.status == InsightStatus.ACTIVE.value,
                        CustomerInsight.category == cat,
                        CustomerInsight.content == txt,
                    )
                    .first()
                )
                if exists:
                    continue

                self.db.add(
                    CustomerInsight(
                        profile_id=profile.id,
                        category=cat,
                        content=txt,
                        source=InsightSource.AI_GENERATED.value,
                        created_by_name="SmartBrain",
                        status=InsightStatus.ACTIVE.value,
                        confidence=conf_val if conf_val is not None else 1.0,
                    )
                )

        self.db.commit()

