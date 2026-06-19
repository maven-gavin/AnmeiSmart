"""流式 Agent 任务取消注册表。"""

from __future__ import annotations

import asyncio
from typing import Dict


class AgentTaskRegistry:
    """管理可取消的 Agent 流式任务。"""

    _cancel_events: Dict[str, asyncio.Event] = {}

    @classmethod
    def register(cls, task_id: str) -> asyncio.Event:
        event = asyncio.Event()
        cls._cancel_events[task_id] = event
        return event

    @classmethod
    def cancel(cls, task_id: str) -> bool:
        event = cls._cancel_events.get(task_id)
        if not event:
            return False
        event.set()
        return True

    @classmethod
    def unregister(cls, task_id: str) -> None:
        cls._cancel_events.pop(task_id, None)

    @classmethod
    def is_cancelled(cls, task_id: str) -> bool:
        event = cls._cancel_events.get(task_id)
        return bool(event and event.is_set())
