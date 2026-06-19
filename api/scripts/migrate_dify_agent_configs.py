#!/usr/bin/env python3
"""
将 agent_configs 从旧 Dify 配置批量迁移到 OpenAI 兼容 LLM（DeepSeek / OpenAI）。

用法（在 api 目录、已激活 venv）:
  # 预览将变更的记录
  python scripts/migrate_dify_agent_configs.py --dry-run

  # 迁移为 DeepSeek（需设置 API Key）
  python scripts/migrate_dify_agent_configs.py --provider deepseek --api-key sk-xxx

  # 从环境变量读取 Key
  export DEEPSEEK_API_KEY=sk-xxx
  python scripts/migrate_dify_agent_configs.py --provider deepseek

  # 仅更新 base_url / capabilities，不修改 api_key
  python scripts/migrate_dify_agent_configs.py --provider openai --skip-api-key

  # 强制更新所有配置（含已是 OpenAI 地址的）
  python scripts/migrate_dify_agent_configs.py --provider deepseek --all
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Any, Dict, Optional, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

PROVIDER_PRESETS: Dict[str, Dict[str, str]] = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat",
        "embedding_model": "text-embedding-3-small",
    },
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "embedding_model": "text-embedding-3-small",
    },
}

# 视为 Dify / 旧网关的 base_url 特征
DIFY_URL_PATTERNS = (
    re.compile(r"localhost(?::\d+)?/v1", re.I),
    re.compile(r"127\.0\.0\.1(?::\d+)?/v1", re.I),
    re.compile(r"dify", re.I),
    re.compile(r"/console/api", re.I),
)


def _looks_like_dify_url(base_url: str) -> bool:
    if not base_url:
        return True
    normalized = base_url.strip().lower()
    if normalized in ("http://localhost/v1", "http://localhost:80/v1"):
        return True
    return any(p.search(normalized) for p in DIFY_URL_PATTERNS)


def _resolve_api_key(provider: str, cli_key: Optional[str]) -> Optional[str]:
    if cli_key:
        return cli_key.strip()
    env_map = {
        "deepseek": "DEEPSEEK_API_KEY",
        "openai": "OPENAI_API_KEY",
    }
    env_name = env_map.get(provider)
    if env_name:
        val = os.environ.get(env_name)
        if val:
            return val.strip()
    return None


def _plan_changes(
    config,
    *,
    provider: str,
    base_url: str,
    model: str,
    embedding_model: str,
    api_key: Optional[str],
    skip_api_key: bool,
    force_all: bool,
) -> Tuple[bool, Dict[str, Any]]:
    changes: Dict[str, Any] = {}
    is_legacy = _looks_like_dify_url(config.base_url or "")

    if force_all or is_legacy:
        if (config.base_url or "").rstrip("/") != base_url.rstrip("/"):
            changes["base_url"] = base_url

    caps = dict(config.capabilities or {})
    caps_changed = False
    if force_all or is_legacy or not caps.get("model"):
        if caps.get("model") != model:
            caps["model"] = model
            caps_changed = True
    if not caps.get("embedding_model"):
        caps["embedding_model"] = embedding_model
        caps_changed = True
    if caps_changed:
        changes["capabilities"] = caps

    if api_key and not skip_api_key:
        changes["api_key"] = api_key

    # 超时：旧 Dify 默认 30s，LLM 流式建议 120s
    if force_all or is_legacy:
        if getattr(config, "timeout_seconds", 30) < 120:
            changes["timeout_seconds"] = 120

    return bool(changes), changes


def main() -> int:
    parser = argparse.ArgumentParser(description="批量迁移 agent_configs（Dify → OpenAI 兼容 LLM）")
    parser.add_argument(
        "--provider",
        choices=["deepseek", "openai"],
        default="deepseek",
        help="目标 LLM 提供商（默认 deepseek）",
    )
    parser.add_argument("--api-key", help="新的 LLM API Key（也可用 DEEPSEEK_API_KEY / OPENAI_API_KEY）")
    parser.add_argument("--base-url", help="覆盖默认 Base URL")
    parser.add_argument("--model", help="覆盖默认模型名")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不写库")
    parser.add_argument("--skip-api-key", action="store_true", help="不更新 api_key")
    parser.add_argument("--all", action="store_true", help="强制处理所有配置（不仅限 Dify URL）")
    args = parser.parse_args()

    preset = PROVIDER_PRESETS[args.provider]
    base_url = (args.base_url or preset["base_url"]).rstrip("/")
    model = args.model or preset["model"]
    embedding_model = preset["embedding_model"]
    api_key = None if args.skip_api_key else _resolve_api_key(args.provider, args.api_key)

    if not args.dry_run and not args.skip_api_key and not api_key:
        print(f"❌ 未提供 API Key。请使用 --api-key 或设置环境变量。")
        return 1

    from sqlalchemy.orm import Session

    from app.common.deps.database import SessionLocal
    from app.ai.models.agent_config import AgentConfig

    db: Session = SessionLocal()
    try:
        configs = db.query(AgentConfig).order_by(AgentConfig.environment, AgentConfig.app_name).all()
        if not configs:
            print("未找到任何 agent_configs 记录。")
            return 0

        updated = 0
        skipped = 0
        would_update = 0
        print(f"共 {len(configs)} 条配置 | 目标: {args.provider} | base_url={base_url} | model={model}")
        if args.dry_run:
            print("【DRY-RUN 模式，不会写入数据库】\n")

        for config in configs:
            should, changes = _plan_changes(
                config,
                provider=args.provider,
                base_url=base_url,
                model=model,
                embedding_model=embedding_model,
                api_key=api_key,
                skip_api_key=args.skip_api_key,
                force_all=args.all,
            )
            if not should:
                skipped += 1
                continue

            print(f"→ [{config.environment}] {config.app_name} ({config.id})")
            for key, val in changes.items():
                if key == "api_key":
                    print("    api_key: ****（将更新）")
                elif key == "capabilities":
                    print(f"    capabilities.model: {val.get('model')}")
                    print(f"    capabilities.embedding_model: {val.get('embedding_model')}")
                else:
                    print(f"    {key}: {val}")

            would_update += 1
            if not args.dry_run:
                if "base_url" in changes:
                    config.base_url = changes["base_url"]
                if "capabilities" in changes:
                    config.capabilities = changes["capabilities"]
                if "timeout_seconds" in changes:
                    config.timeout_seconds = changes["timeout_seconds"]
                if "api_key" in changes:
                    config.api_key = changes["api_key"]
                updated += 1

        if args.dry_run:
            print(f"\n预览完成：将更新 {would_update} 条，跳过 {skipped} 条。")
        else:
            db.commit()
            print(f"\n✅ 迁移完成：已更新 {updated} 条，跳过 {skipped} 条。")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"❌ 迁移失败: {exc}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
