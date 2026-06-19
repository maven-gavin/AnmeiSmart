"""解析对话 inputs 中的文件引用。"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.ai.rag.index_service import RagIndexService
from app.common.models.file import File

logger = logging.getLogger(__name__)

MAX_FILE_CHARS = 12000


class InputContextResolver:
    """将 inputs / 文件 ID 解析为可注入 LLM 的文本上下文。"""

    def __init__(self, db: Session):
        self.db = db
        self.rag = RagIndexService(db)

    def enrich_user_message(self, message: str, inputs: Optional[Dict[str, Any]]) -> str:
        if not inputs:
            return message

        sections: List[str] = [message]
        plain_inputs: Dict[str, Any] = {}

        for key, value in inputs.items():
            file_ids = self._extract_file_ids(key, value)
            for file_id in file_ids:
                excerpt = self._load_file_excerpt(file_id)
                if excerpt:
                    sections.append(f"\n[附件: {key}]\n{excerpt}")

            if "file" not in key.lower() and not self._looks_like_file_id(value):
                plain_inputs[key] = value

        if plain_inputs:
            sections.append(f"\n[参数]\n{json.dumps(plain_inputs, ensure_ascii=False)}")

        return "\n".join(sections).strip()

    @staticmethod
    def _extract_file_ids(key: str, value: Any) -> List[str]:
        ids: List[str] = []
        if "file" in key.lower():
            if isinstance(value, list):
                ids.extend(str(v) for v in value if v)
            elif value:
                ids.append(str(value))
        elif isinstance(value, str) and len(value) == 36 and value.count("-") == 4:
            ids.append(value)
        return ids

    @staticmethod
    def _looks_like_file_id(value: Any) -> bool:
        return isinstance(value, str) and len(value) == 36 and value.count("-") == 4

    def _load_file_excerpt(self, file_id: str) -> Optional[str]:
        record = self.db.query(File).filter(File.id == file_id).first()
        if not record:
            return None
        try:
            raw = self.rag.load_file_bytes(record)
            text = raw.decode("utf-8", errors="ignore").strip()
            if not text:
                return f"(二进制文件 {record.file_name}，大小 {record.file_size} 字节)"
            if len(text) > MAX_FILE_CHARS:
                return text[:MAX_FILE_CHARS] + "\n...(已截断)"
            return text
        except Exception as exc:
            logger.warning("读取附件失败 file_id=%s: %s", file_id, exc)
            return None
