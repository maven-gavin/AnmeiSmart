"""SSE 事件发射器（保持前端协议兼容）。"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Dict, Optional


def new_task_id() -> str:
    return str(uuid.uuid4())


def emit_event(payload: Dict[str, Any]) -> bytes:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")


def emit_error(message: str, *, status: Optional[int] = None) -> bytes:
    payload: Dict[str, Any] = {"event": "error", "message": message}
    if status is not None:
        payload["status"] = status
    return emit_event(payload)


def emit_message_chunk(
    *,
    answer: str,
    conversation_id: str,
    message_id: str,
    task_id: str,
    event: str = "message",
) -> bytes:
    return emit_event(
        {
            "event": event,
            "answer": answer,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "task_id": task_id,
            "id": message_id,
            "created_at": int(datetime.now().timestamp()),
        }
    )


def emit_agent_thought(
    *,
    thought: str,
    conversation_id: str,
    message_id: str,
    task_id: str,
) -> bytes:
    return emit_event(
        {
            "event": "agent_thought",
            "thought": thought,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "task_id": task_id,
            "id": message_id,
            "created_at": int(datetime.now().timestamp()),
        }
    )


def emit_message_end(
    *,
    conversation_id: str,
    message_id: str,
    task_id: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> bytes:
    payload: Dict[str, Any] = {
        "event": "message_end",
        "conversation_id": conversation_id,
        "message_id": message_id,
        "task_id": task_id,
        "id": message_id,
    }
    if metadata:
        payload["metadata"] = metadata
    return emit_event(payload)
