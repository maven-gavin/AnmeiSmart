"""
渠道身份映射管理 API（管理员/运营使用）
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.identity_access.deps import get_current_user
from app.identity_access.deps.permission_deps import check_user_any_role
from app.identity_access.models.user import User
from app.channels.deps.channel_deps import get_channel_identity_service
from app.channels.services.channel_identity_service import ChannelIdentityService
from app.channels.schemas.channel_identity import (
    ChannelIdentityBindRequest,
    ChannelIdentityInfo,
    ChannelCustomerMergeRequest,
)
from app.core.api import BusinessException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/channels", tags=["channels"])


async def _require_channel_admin(current_user: User) -> None:
    ok = await check_user_any_role(current_user, ["operator", "administrator", "admin"])
    if not ok:
        raise HTTPException(status_code=403, detail="无权管理渠道身份映射")


@router.post("/identities/bind", response_model=ChannelIdentityInfo)
async def bind_channel_identity(
    request: ChannelIdentityBindRequest,
    current_user: User = Depends(get_current_user),
    service: ChannelIdentityService = Depends(get_channel_identity_service),
):
    """
    绑定/迁移渠道身份到指定 customer(User)。

    使用场景：
    - 避免重复建客户：提前把 peer_id 绑定到一个已有 customer
    - 纠错：把已创建的错误映射迁移到正确 customer
    """
    try:
        await _require_channel_admin(current_user)
        identity = service.bind_identity(
            channel_type=request.channel_type,
            peer_id=request.peer_id,
            customer_user_id=request.customer_user_id,
            peer_name=request.peer_name,
            extra_data=request.extra_data,
            migrate_conversations=request.migrate_conversations,
        )
        return ChannelIdentityInfo.model_validate(identity)
    except HTTPException:
        raise
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"绑定渠道身份失败: err={e}", exc_info=True)
        raise HTTPException(status_code=500, detail="绑定渠道身份失败")


@router.get("/identities/by-customer/{customer_user_id}", response_model=List[ChannelIdentityInfo])
async def list_channel_identities_by_customer(
    customer_user_id: str,
    current_user: User = Depends(get_current_user),
    service: ChannelIdentityService = Depends(get_channel_identity_service),
):
    """查询某个 customer(User) 绑定的所有渠道身份"""
    try:
        await _require_channel_admin(current_user)
        items = service.list_by_customer(customer_user_id=customer_user_id)
        return [ChannelIdentityInfo.model_validate(x) for x in items]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询渠道身份失败: err={e}", exc_info=True)
        raise HTTPException(status_code=500, detail="查询渠道身份失败")


@router.get("/identities/lookup", response_model=Optional[ChannelIdentityInfo])
async def lookup_channel_identity(
    channel_type: str = Query(..., min_length=1, max_length=50),
    peer_id: str = Query(..., min_length=1, max_length=255),
    current_user: User = Depends(get_current_user),
    service: ChannelIdentityService = Depends(get_channel_identity_service),
):
    """按 channel_type + peer_id 查询映射（用于排查/调试）"""
    try:
        await _require_channel_admin(current_user)
        identity = service.get_by_type_peer(channel_type=channel_type, peer_id=peer_id)
        return ChannelIdentityInfo.model_validate(identity) if identity else None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询渠道身份失败: err={e}", exc_info=True)
        raise HTTPException(status_code=500, detail="查询渠道身份失败")


@router.post("/identities/merge-customers", response_model=dict)
async def merge_customer_channel_identities(
    request: ChannelCustomerMergeRequest,
    current_user: User = Depends(get_current_user),
    service: ChannelIdentityService = Depends(get_channel_identity_service),
):
    """将 source customer 的所有渠道身份合并到 target customer（常用于去重/纠错）"""
    try:
        await _require_channel_admin(current_user)
        moved = service.merge_customer_identities(
            source_customer_user_id=request.source_customer_user_id,
            target_customer_user_id=request.target_customer_user_id,
            migrate_conversations=request.migrate_conversations,
        )
        return {"moved_identities": moved}
    except HTTPException:
        raise
    except BusinessException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"合并渠道身份失败: err={e}", exc_info=True)
        raise HTTPException(status_code=500, detail="合并渠道身份失败")

