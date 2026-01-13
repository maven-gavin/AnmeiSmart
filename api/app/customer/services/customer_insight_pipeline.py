"""
客户画像洞察 Pipeline

用于在“客户消息写入成功”后，异步触发洞察提取与落库。

设计目标：
- 不阻塞主请求（发送消息/入站消息）
- 不引入跨模块复杂依赖（Chat 模块只需调用一个 enqueue 函数）
- 失败不影响主流程（仅记录日志）
"""

import asyncio
import logging

from app.common.deps.database import SessionLocal
from app.customer.services.customer_insight_ai_service import CustomerInsightAIService

logger = logging.getLogger(__name__)


async def _run_customer_insight_job(customer_id: str, conversation_id: str, message_id: str) -> None:
    db = SessionLocal()
    try:
        service = CustomerInsightAIService(db=db)
        await service.analyze_and_persist_from_message(
            customer_id=customer_id,
            conversation_id=conversation_id,
            message_id=message_id,
        )
    except Exception as e:
        logger.warning(
            f"CustomerInsightPipeline: 洞察任务失败（已降级）: customer_id={customer_id}, "
            f"conversation_id={conversation_id}, message_id={message_id}, err={e}",
            exc_info=True,
        )
    finally:
        db.close()


def enqueue_customer_insight_job(customer_id: str, conversation_id: str, message_id: str) -> None:
    """
    在当前事件循环中异步触发洞察任务。
    注意：该函数必须在 async 环境中调用（例如 FastAPI async endpoint）。
    """
    try:
        asyncio.create_task(_run_customer_insight_job(customer_id, conversation_id, message_id))
    except Exception as e:
        logger.warning(
            f"CustomerInsightPipeline: create_task 失败（已跳过）: customer_id={customer_id}, "
            f"conversation_id={conversation_id}, message_id={message_id}, err={e}",
            exc_info=True,
        )

