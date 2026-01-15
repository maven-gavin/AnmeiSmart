import asyncio
import logging
from typing import Optional

from app.common.deps.database import SessionLocal
from app.channels.services.channel_config_service import ChannelConfigService
from app.channels.services.channel_service import ChannelService
from app.channels.services.wechat_work_archive_service import WeChatWorkArchiveService
from app.channels.services.wechat_work_archive_ingest import ingest_decrypted_messages

logger = logging.getLogger(__name__)

_archive_task: Optional[asyncio.Task] = None


async def _poll_loop() -> None:
    while True:
        db = SessionLocal()
        try:
            config_service = ChannelConfigService(db)
            cfg = config_service.get_by_type(channel_type="wechat_work_archive")
            if not cfg or not cfg.is_active or not isinstance(cfg.config, dict):
                await asyncio.sleep(30)
                continue

            poll_enabled = bool(cfg.config.get("poll_enabled", False))
            interval = int(cfg.config.get("poll_interval_seconds", 60))
            limit = int(cfg.config.get("poll_limit", 100))

            if not poll_enabled:
                await asyncio.sleep(max(interval, 10))
                continue

            archive_service = WeChatWorkArchiveService(db=db)
            messages, _ = await archive_service.pull_chatdata(limit=limit)

            channel_service = ChannelService(db=db, broadcasting_service=None)
            await ingest_decrypted_messages(messages, channel_service=channel_service)

            await asyncio.sleep(max(interval, 10))
        except Exception as e:
            logger.warning(f"会话内容存档轮询失败（已忽略）: {e}", exc_info=True)
            await asyncio.sleep(30)
        finally:
            db.close()


def start_archive_polling() -> None:
    global _archive_task
    if _archive_task and not _archive_task.done():
        return
    _archive_task = asyncio.create_task(_poll_loop())
    logger.info("会话内容存档轮询任务已启动")


async def stop_archive_polling() -> None:
    global _archive_task
    if _archive_task:
        _archive_task.cancel()
        try:
            await _archive_task
        except asyncio.CancelledError:
            pass
        _archive_task = None
        logger.info("会话内容存档轮询任务已停止")
