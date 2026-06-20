#!/usr/bin/env python3
"""
清理已下线的渠道（tag=channel）历史数据。

用法:
  cd api
  python scripts/cleanup_channel_data.py --dry-run   # 仅统计
  python scripts/cleanup_channel_data.py             # 执行删除（需确认）
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text

from app.common.deps.database import SessionLocal


def main() -> None:
    parser = argparse.ArgumentParser(description="清理 tag=channel 的历史会话与消息")
    parser.add_argument("--dry-run", action="store_true", help="仅统计，不删除")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        conv_count = db.execute(
            text("SELECT COUNT(*) FROM conversations WHERE tag = 'channel'")
        ).scalar_one()
        msg_count = db.execute(
            text(
                """
                SELECT COUNT(*) FROM messages m
                JOIN conversations c ON c.id = m.conversation_id
                WHERE c.tag = 'channel'
                """
            )
        ).scalar_one()
        part_count = db.execute(
            text(
                """
                SELECT COUNT(*) FROM conversation_participants cp
                JOIN conversations c ON c.id = cp.conversation_id
                WHERE c.tag = 'channel'
                """
            )
        ).scalar_one()

        print(f"渠道会话: {conv_count}")
        print(f"关联消息: {msg_count}")
        print(f"关联参与者: {part_count}")

        if args.dry_run:
            print("dry-run 模式，未执行删除")
            return

        if conv_count == 0:
            print("无数据需要清理")
            return

        confirm = input("确认删除以上渠道数据？输入 yes 继续: ").strip().lower()
        if confirm != "yes":
            print("已取消")
            return

        db.execute(
            text(
                """
                DELETE FROM messages
                WHERE conversation_id IN (SELECT id FROM conversations WHERE tag = 'channel')
                """
            )
        )
        db.execute(
            text(
                """
                DELETE FROM conversation_participants
                WHERE conversation_id IN (SELECT id FROM conversations WHERE tag = 'channel')
                """
            )
        )
        db.execute(text("DELETE FROM conversations WHERE tag = 'channel'"))
        db.commit()
        print("清理完成")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
