"""
会话内容存档拉取入口
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.core.api import ApiResponse
from app.identity_access.deps.permission_deps import require_any_role
from app.identity_access.models.user import User
from app.channels.services.wechat_work_archive_service import WeChatWorkArchiveService
from app.channels.services.wechat_work_archive_ingest import ingest_decrypted_messages
from app.channels.services.channel_service import ChannelService
from app.channels.deps.channel_deps import get_channel_service
from app.common.deps.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/channels/archive", tags=["channels-archive"])


@router.post(
    "/pull",
    response_model=ApiResponse[dict],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_any_role(["admin", "admin", "operator"]))],
)
async def pull_wechat_work_archive(
    seq: Optional[int] = Query(None, description="起始 seq，留空则使用上次记录"),
    limit: int = Query(100, ge=1, le=1000, description="每次拉取数量"),
    current_user: User = Depends(require_any_role(["admin", "admin", "operator"])),
    db: Session = Depends(get_db),
    channel_service: ChannelService = Depends(get_channel_service),
):
    """
    拉取企业微信会话内容存档，解密后投递到渠道入站处理。
    """
    try:
        archive_service = WeChatWorkArchiveService(db=db)
        messages, next_seq = await archive_service.pull_chatdata(seq=seq, limit=limit)

        processed = await ingest_decrypted_messages(messages, channel_service=channel_service)

        return ApiResponse.success(
            {
                "requested_seq": seq,
                "next_seq": next_seq,
                "raw_count": len(messages),
                "processed": processed,
            }
        )
    except Exception as e:
        logger.error(f"拉取会话存档失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="拉取会话存档失败")

