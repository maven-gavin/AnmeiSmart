#!/usr/bin/env python3
"""
启用 PostgreSQL pgvector 扩展并验证 RAG 可用性。

用法（在 api 目录、已激活 venv）:
  python scripts/setup_pgvector.py
  python scripts/setup_pgvector.py --check-only
"""

from __future__ import annotations

import argparse
import os
import sys

# 将 api 根目录加入 path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def _get_database_url() -> str:
    from app.core.config import get_settings

    return get_settings().DATABASE_URL


def enable_pgvector(database_url: str) -> None:
    import psycopg2
    from urllib.parse import urlparse

    parsed = urlparse(database_url.replace("postgresql+asyncpg://", "postgresql://"))
    conn = psycopg2.connect(
        host=parsed.hostname or "localhost",
        port=parsed.port or 5432,
        user=parsed.username or "postgres",
        password=parsed.password,
        database=(parsed.path or "/anmeismart").lstrip("/"),
        connect_timeout=10,
    )
    conn.autocommit = True
    try:
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            row = cur.fetchone()
            if not row:
                raise RuntimeError("pgvector 扩展创建后仍未检测到")
            print(f"✅ pgvector 已启用，版本: {row[0]}")
    finally:
        conn.close()


def check_pgvector(database_url: str) -> bool:
    import psycopg2
    from urllib.parse import urlparse

    parsed = urlparse(database_url.replace("postgresql+asyncpg://", "postgresql://"))
    try:
        conn = psycopg2.connect(
            host=parsed.hostname or "localhost",
            port=parsed.port or 5432,
            user=parsed.username or "postgres",
            password=parsed.password,
            database=(parsed.path or "/anmeismart").lstrip("/"),
            connect_timeout=5,
        )
    except Exception as exc:
        print(f"❌ 无法连接数据库: {exc}")
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT extversion FROM pg_extension WHERE extname = 'vector'")
            row = cur.fetchone()
            if row:
                print(f"✅ pgvector 已安装，版本: {row[0]}")
                return True
            print("❌ pgvector 未安装")
            return False
    finally:
        conn.close()


def print_help() -> None:
    print(
        """
未检测到 pgvector，可按以下方式之一解决：

【推荐】使用项目内置 PostgreSQL（Docker，已预装 pgvector）:
  cd /path/to/AnmeiSmart
  docker compose up -d postgres
  # .env 中设置:
  # DATABASE_URL=postgresql://postgres:anmei_pg_pass@localhost:5432/anmeismart

【macOS 本地 PostgreSQL】Homebrew 安装 pgvector:
  brew install pgvector
  # PostgreSQL 14 示例:
  brew install pgvector
  # 重启 PostgreSQL 后执行:
  python scripts/setup_pgvector.py

【已有 Docker Postgres 容器】进入容器安装（仅当镜像不含 pgvector）:
  请改用官方镜像 pgvector/pgvector:pg16

文档: https://github.com/pgvector/pgvector#installation
"""
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="启用/检查 PostgreSQL pgvector 扩展")
    parser.add_argument("--check-only", action="store_true", help="仅检查，不尝试创建扩展")
    args = parser.parse_args()

    database_url = _get_database_url()
    host_hint = database_url.split("@")[-1] if "@" in database_url else database_url
    print(f"📊 目标数据库: {host_hint}")

    if args.check_only:
        return 0 if check_pgvector(database_url) else 1

    if check_pgvector(database_url):
        return 0

    try:
        enable_pgvector(database_url)
        return 0
    except Exception as exc:
        print(f"❌ 启用 pgvector 失败: {exc}")
        print_help()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
