"""
渠道配置管理（管理员/运营）
"""
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.core.api import ApiResponse
from app.identity_access.deps import get_current_user
from app.identity_access.deps.permission_deps import check_user_any_role
from app.identity_access.models.user import User
from app.channels.deps.channel_deps import get_channel_config_service
from app.channels.services.channel_config_service import ChannelConfigService
from app.channels.schemas.channel_config import ChannelConfigInfo, ChannelConfigUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/channels/configs", tags=["channels-configs"])


async def _require_channel_admin(current_user: User) -> None:
    ok = await check_user_any_role(current_user, ["operator", "administrator", "admin"])
    if not ok:
        raise HTTPException(status_code=403, detail="无权管理渠道配置")


@router.get("/{channel_type}", response_model=ApiResponse[ChannelConfigInfo])
async def get_channel_config(
    channel_type: str,
    current_user: User = Depends(get_current_user),
    service: ChannelConfigService = Depends(get_channel_config_service),
):
    try:
        await _require_channel_admin(current_user)
        row = service.get_by_type(channel_type=channel_type)
        if not row:
            raise HTTPException(status_code=404, detail="渠道配置不存在")
        return ApiResponse.success(ChannelConfigInfo.model_validate(row))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询渠道配置失败: err={e}", exc_info=True)
        raise HTTPException(status_code=500, detail="查询渠道配置失败")


@router.put("/{channel_type}", response_model=ApiResponse[ChannelConfigInfo])
async def upsert_channel_config(
    channel_type: str,
    request: ChannelConfigUpdate,
    current_user: User = Depends(get_current_user),
    service: ChannelConfigService = Depends(get_channel_config_service),
):
    try:
        await _require_channel_admin(current_user)
        current = service.get_by_type(channel_type=channel_type)
        name = request.name or (current.name if current else channel_type)
        config = request.config if request.config is not None else (current.config if current else {})
        is_active = request.is_active if request.is_active is not None else (current.is_active if current else True)
        row = service.upsert_config(
            channel_type=channel_type,
            name=name,
            config=config,
            is_active=is_active,
        )
        return ApiResponse.success(ChannelConfigInfo.model_validate(row))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新渠道配置失败: err={e}", exc_info=True)
        raise HTTPException(status_code=500, detail="更新渠道配置失败")
