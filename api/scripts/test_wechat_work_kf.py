#!/usr/bin/env python
"""
企业微信 - 微信客服（KF）配置测试脚本
1) 检查环境变量
2) 获取 access_token
3) 列出 open_kfid（客服账号）
"""
import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def main() -> int:
    corp_id = os.getenv("WECHAT_WORK_CORP_ID")
    kf_secret = os.getenv("WECHAT_WORK_KF_SECRET")
    kf_token = os.getenv("WECHAT_WORK_KF_TOKEN")
    kf_aes = os.getenv("WECHAT_WORK_KF_ENCODING_AES_KEY")
    kf_open_kfid = os.getenv("WECHAT_WORK_KF_OPEN_KFID")

    missing = []
    if not corp_id:
        missing.append("WECHAT_WORK_CORP_ID")
    if not kf_secret:
        missing.append("WECHAT_WORK_KF_SECRET")

    if missing:
        logger.error(f"❌ 缺少环境变量: {', '.join(missing)}")
        return 1

    logger.info("✅ 基础配置存在")
    logger.info(f"  - WECHAT_WORK_CORP_ID: {corp_id[:10]}...")
    logger.info(f"  - WECHAT_WORK_KF_SECRET: {kf_secret[:10]}...")
    logger.info(f"  - WECHAT_WORK_KF_TOKEN: {'已配置' if kf_token else '未配置（回调验签会受影响）'}")
    logger.info(f"  - WECHAT_WORK_KF_ENCODING_AES_KEY: {'已配置' if kf_aes else '未配置（回调解密会受影响）'}")
    logger.info(f"  - WECHAT_WORK_KF_OPEN_KFID: {kf_open_kfid or '未配置（需要选择一个客服账号）'}")

    from app.channels.adapters.wechat_work.kf_client import WeChatWorkKfClient

    client = WeChatWorkKfClient(corp_id=corp_id, secret=kf_secret)
    token = await client.get_access_token()
    logger.info(f"✅ 获取 access_token 成功: {token[:20]}...")

    accounts = await client.list_accounts()
    logger.info(f"✅ 客服账号数量: {len(accounts)}")
    for acc in accounts[:20]:
        logger.info(f"  - open_kfid={acc.get('open_kfid')} name={acc.get('name')}")

    if not kf_open_kfid and accounts:
        hint = accounts[0].get("open_kfid")
        logger.info("")
        logger.info("💡 建议在 api/.env 中设置：")
        logger.info(f"WECHAT_WORK_KF_OPEN_KFID={hint}")

    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))


