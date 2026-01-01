"""add_files_table_and_migrate_to_file_id

Revision ID: 76f686c16c95
Revises: <SET_DOWN_REVISION>
Create Date: 2026-01-01 11:09:56.660682

说明：
- 严格按 docs/file-architecture-optimization-analysis.md 执行：仅新增 files 表 + 历史数据迁移（upload_sessions/messages/users/digital_humans）
- 不包含任何无关的 autogenerate 变更（否则易引入枚举转换/字段改动风险）
"""

from __future__ import annotations

import json
import re
import uuid
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "76f686c16c95"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_UUID_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def _detect_file_type(mime_type: str) -> str:
    if not mime_type:
        return "document"
    if mime_type.startswith("image/"):
        return "image"
    if mime_type.startswith("audio/"):
        return "audio"
    if mime_type.startswith("video/"):
        return "video"
    if mime_type in ("application/zip", "application/x-rar-compressed"):
        return "archive"
    return "document"


def _extract_object_name_from_url(url: str) -> str | None:
    if not url:
        return None
    if url.startswith("http") and "/chat-files/" in url:
        return url.split("/chat-files/", 1)[1].split("?", 1)[0].split("#", 1)[0]
    if url.startswith("/chat-files/"):
        return url[len("/chat-files/") :].split("?", 1)[0].split("#", 1)[0]
    # 兼容历史直接存 object_name 的场景（不含协议、不以 / 开头）
    if not url.startswith("http") and not url.startswith("/") and not url.startswith("data:") and not url.startswith("blob:"):
        return url.split("?", 1)[0].split("#", 1)[0]
    return None


def _extract_avatar_object_name(value: str) -> str | None:
    """
    头像历史值可能是：
    - http(s)://.../files/public/{object_name}
    - http(s)://.../chat-files/{object_name}
    - /chat-files/{object_name}
    - 直接 object_name（包含 avatars/ 前缀路径）
    """
    if not value:
        return None
    if "/files/public/" in value:
        return value.split("/files/public/", 1)[1].split("?", 1)[0].split("#", 1)[0]
    if "/chat-files/" in value:
        return value.split("/chat-files/", 1)[1].split("?", 1)[0].split("#", 1)[0]
    if value.startswith("/chat-files/"):
        return value[len("/chat-files/") :].split("?", 1)[0].split("#", 1)[0]
    if not value.startswith("http") and not value.startswith("/") and "avatars/" in value:
        return value.split("?", 1)[0].split("#", 1)[0]
    return None


def upgrade() -> None:
    # 1) 创建 files 表
    op.create_table(
        "files",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False, comment="文件ID"),
        sa.Column("object_name", sa.String(length=500), nullable=False, unique=True, comment="MinIO对象名"),
        sa.Column("file_name", sa.String(length=255), nullable=False, comment="原始文件名"),
        sa.Column("file_size", sa.BigInteger(), nullable=False, comment="文件大小（字节）"),
        sa.Column("mime_type", sa.String(length=100), nullable=False, comment="MIME类型"),
        sa.Column("file_type", sa.String(length=50), nullable=False, comment="文件类型：image/document/audio/video/archive"),
        sa.Column("md5", sa.String(length=50), nullable=True, comment="MD5校验值"),
        sa.Column("user_id", sa.String(length=36), nullable=False, comment="上传用户ID"),
        sa.Column("business_type", sa.String(length=50), nullable=True, comment="业务类型：avatar/message/document"),
        sa.Column("business_id", sa.String(length=36), nullable=True, comment="关联业务对象ID"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("false"), comment="是否公开访问（例如头像）"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("created_by", sa.String(length=36), nullable=True, comment="创建人ID"),
        sa.Column("updated_by", sa.String(length=36), nullable=True, comment="修改人ID"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        comment="文件表，统一管理所有文件信息",
    )
    op.create_index("idx_file_user_id", "files", ["user_id"], unique=False)
    op.create_index("idx_file_business", "files", ["business_type", "business_id"], unique=False)
    op.create_index("idx_file_object_name", "files", ["object_name"], unique=False)

    connection = op.get_bind()

    # 2) upload_sessions -> files（completed + final_object_name）
    print("[migrate] upload_sessions -> files ...")
    try:
        sessions = connection.execute(
            text(
                """
                SELECT final_object_name, file_name, file_size, content_type, user_id, business_type, business_id, created_at
                FROM upload_sessions
                WHERE status = 'completed' AND final_object_name IS NOT NULL
                """
            )
        ).fetchall()

        for row in sessions:
            try:
                existing = connection.execute(
                    text("SELECT id FROM files WHERE object_name = :object_name"),
                    {"object_name": row.final_object_name},
                ).fetchone()
                if existing:
                    continue

                fid = str(uuid.uuid4())
                connection.execute(
                    text(
                        """
                        INSERT INTO files (id, object_name, file_name, file_size, mime_type, file_type, user_id, business_type, business_id, is_public, created_at, updated_at)
                        VALUES (:id, :object_name, :file_name, :file_size, :mime_type, :file_type, :user_id, :business_type, :business_id, false, :created_at, :updated_at)
                        """
                    ),
                    {
                        "id": fid,
                        "object_name": row.final_object_name,
                        "file_name": row.file_name,
                        "file_size": row.file_size or 0,
                        "mime_type": row.content_type or "application/octet-stream",
                        "file_type": _detect_file_type(row.content_type or ""),
                        "user_id": row.user_id,
                        "business_type": row.business_type,
                        "business_id": row.business_id,
                        "created_at": row.created_at,
                        "updated_at": row.created_at,
                    },
                )
            except Exception as e:
                print(f"[migrate][warn] upload_session -> files failed: object_name={row.final_object_name}, err={e}")
    except Exception as e:
        print(f"[migrate][warn] scan upload_sessions failed: {e}")

    # 3) messages.content media_info.url -> media_info.file_id
    # 说明：历史数据结构可能不同，这里只处理 dict 且存在 media_info/url 的情况
    print("[migrate] messages.content url -> file_id ...")
    try:
        rows = connection.execute(
            text(
                """
                SELECT id, content, conversation_id, sender_id
                FROM messages
                WHERE content IS NOT NULL
                """
            )
        ).fetchall()

        for row in rows:
            try:
                content = row.content
                if isinstance(content, str):
                    content = json.loads(content)
                if not isinstance(content, dict):
                    continue

                media_info = content.get("media_info")
                if not isinstance(media_info, dict):
                    continue

                # 已迁移则跳过
                if media_info.get("file_id"):
                    continue

                url = media_info.get("url") or ""
                object_name = _extract_object_name_from_url(url)
                if not object_name:
                    continue

                file_row = connection.execute(
                    text("SELECT id FROM files WHERE object_name = :object_name"),
                    {"object_name": object_name},
                ).fetchone()

                if not file_row:
                    fid = str(uuid.uuid4())
                    mime_type = media_info.get("mime_type") or "application/octet-stream"
                    connection.execute(
                        text(
                            """
                            INSERT INTO files (id, object_name, file_name, file_size, mime_type, file_type, user_id, business_type, business_id, is_public, created_at, updated_at)
                            VALUES (:id, :object_name, :file_name, :file_size, :mime_type, :file_type, :user_id, 'message', :business_id, false, now(), now())
                            """
                        ),
                        {
                            "id": fid,
                            "object_name": object_name,
                            "file_name": media_info.get("name") or "unknown",
                            "file_size": int(media_info.get("size_bytes") or 0),
                            "mime_type": mime_type,
                            "file_type": _detect_file_type(mime_type),
                            "user_id": row.sender_id or "system",
                            "business_id": row.conversation_id,
                        },
                    )
                    file_id_to_use = fid
                else:
                    file_id_to_use = file_row.id

                # 更新消息 content：写入 file_id，并移除 url（严格不向后兼容）
                media_info["file_id"] = file_id_to_use
                if "url" in media_info:
                    media_info.pop("url", None)
                content["media_info"] = media_info

                connection.execute(
                    text("UPDATE messages SET content = :content WHERE id = :id"),
                    {"content": json.dumps(content, ensure_ascii=False), "id": row.id},
                )
            except Exception as e:
                print(f"[migrate][warn] message migrate failed: message_id={row.id}, err={e}")
    except Exception as e:
        print(f"[migrate][warn] scan messages failed: {e}")

    # 4) users.avatar / digital_humans.avatar url -> file_id
    # 严格：迁移后字段只存 file_id
    print("[migrate] avatars url -> file_id ...")
    for table_name, business_type, is_public in (
        ("users", "avatar", True),
        ("digital_humans", "avatar", True),
    ):
        try:
            avatars = connection.execute(
                text(f"SELECT id, avatar FROM {table_name} WHERE avatar IS NOT NULL AND avatar != ''")
            ).fetchall()
            for row in avatars:
                try:
                    avatar = row.avatar
                    if not avatar or _UUID_RE.match(avatar):
                        continue

                    object_name = _extract_avatar_object_name(avatar)
                    if not object_name:
                        continue

                    file_row = connection.execute(
                        text("SELECT id FROM files WHERE object_name = :object_name"),
                        {"object_name": object_name},
                    ).fetchone()

                    if not file_row:
                        fid = str(uuid.uuid4())
                        connection.execute(
                            text(
                                """
                                INSERT INTO files (id, object_name, file_name, file_size, mime_type, file_type, user_id, business_type, business_id, is_public, created_at, updated_at)
                                VALUES (:id, :object_name, :file_name, 0, 'image/jpeg', 'image', :user_id, :business_type, :business_id, :is_public, now(), now())
                                """
                            ),
                            {
                                "id": fid,
                                "object_name": object_name,
                                "file_name": object_name.split("/")[-1],
                                "user_id": "system",
                                "business_type": business_type,
                                "business_id": row.id,
                                "is_public": bool(is_public),
                            },
                        )
                        file_id_to_use = fid
                    else:
                        file_id_to_use = file_row.id

                    connection.execute(
                        text(f"UPDATE {table_name} SET avatar = :file_id WHERE id = :id"),
                        {"file_id": file_id_to_use, "id": row.id},
                    )
                except Exception as e:
                    print(f"[migrate][warn] {table_name}.avatar migrate failed: id={row.id}, err={e}")
        except Exception as e:
            print(f"[migrate][warn] scan {table_name}.avatar failed: {e}")


def downgrade() -> None:
    # 回滚：删除 files 表（不回滚已迁移的 content/avatar 字段，避免破坏数据）
    op.drop_index("idx_file_object_name", table_name="files")
    op.drop_index("idx_file_business", table_name="files")
    op.drop_index("idx_file_user_id", table_name="files")
    op.drop_table("files")

