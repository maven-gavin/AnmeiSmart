"""
数字人管理API端点

遵循 docs/API_ERROR_HANDLING_STANDARD.md：
- 使用 ApiResponse 统一响应格式
- 使用 BusinessException/SystemException + ErrorCode 统一错误处理
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, status

from app.core.api import ApiResponse, BusinessException, ErrorCode, SystemException
from app.identity_access.deps import get_current_user
from app.identity_access.models.user import User
from ..deps.digital_humans import get_digital_human_service
from ..schemas.digital_human import (
    AddAgentConfigRequest,
    CreateDigitalHumanRequest,
    DigitalHumanAgentConfigInfo,
    DigitalHumanResponse,
    UpdateAgentConfigRequest,
    UpdateDigitalHumanRequest,
)
from ..services.digital_human_service import DigitalHumanService

logger = logging.getLogger(__name__)
router = APIRouter()


def _handle_unexpected_error(message: str, exc: Exception) -> SystemException:
    """封装系统异常，符合统一错误处理规范"""
    logger.error(f"{message}: {exc}", exc_info=True)
    return SystemException(message=message, code=ErrorCode.SYSTEM_ERROR)


@router.get("/", response_model=ApiResponse[list[DigitalHumanResponse]])
async def get_digital_humans(
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service),
) -> ApiResponse[list[DigitalHumanResponse]]:
    """获取当前用户的数字人列表"""
    try:
        digital_humans = service.get_user_digital_humans(current_user.id)
        return ApiResponse.success(digital_humans, message="获取数字人列表成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取数字人列表失败", e)


@router.get(
    "/{digital_human_id}",
    response_model=ApiResponse[DigitalHumanResponse],
)
async def get_digital_human(
    digital_human_id: str,
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service),
) -> ApiResponse[DigitalHumanResponse]:
    """获取数字人详情"""
    try:
        digital_human = service.get_digital_human_by_id(digital_human_id, current_user.id)

        if not digital_human:
            raise BusinessException(
                "数字人不存在或无权限访问",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return ApiResponse.success(digital_human, message="获取数字人详情成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取数字人详情失败", e)


@router.post(
    "/",
    response_model=ApiResponse[DigitalHumanResponse],
    status_code=status.HTTP_201_CREATED,
)
async def create_digital_human(
    data: CreateDigitalHumanRequest,
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service),
) -> ApiResponse[DigitalHumanResponse]:
    """创建数字人"""
    try:
        digital_human = service.create_digital_human(current_user.id, data)
        return ApiResponse.success(digital_human, message="创建数字人成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("创建数字人失败", e)


@router.put(
    "/{digital_human_id}",
    response_model=ApiResponse[DigitalHumanResponse],
)
async def update_digital_human(
    digital_human_id: str,
    data: UpdateDigitalHumanRequest,
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service),
) -> ApiResponse[DigitalHumanResponse]:
    """更新数字人信息"""
    try:
        digital_human = service.update_digital_human(digital_human_id, current_user.id, data)

        if not digital_human:
            raise BusinessException(
                "数字人不存在或无权限修改",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return ApiResponse.success(digital_human, message="更新数字人成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("更新数字人失败", e)


@router.delete(
    "/{digital_human_id}",
    response_model=ApiResponse[None],
)
async def delete_digital_human(
    digital_human_id: str,
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service),
) -> ApiResponse[None]:
    """删除数字人（系统创建的不可删除）"""
    try:
        success = service.delete_digital_human(digital_human_id, current_user.id)

        if not success:
            raise BusinessException(
                "数字人不存在、无权限删除或为系统创建",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return ApiResponse.success(message="删除数字人成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("删除数字人失败", e)


@router.get(
    "/{digital_human_id}/agents",
    response_model=ApiResponse[List[DigitalHumanAgentConfigInfo]],
)
async def get_digital_human_agents(
    digital_human_id: str,
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service),
) -> ApiResponse[List[DigitalHumanAgentConfigInfo]]:
    """获取数字人的智能体配置列表"""
    try:
        agent_configs = service.get_digital_human_agents(digital_human_id, current_user.id)
        return ApiResponse.success(agent_configs, message="获取智能体配置成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("获取数字人智能体配置失败", e)


@router.post(
    "/{digital_human_id}/agents",
    response_model=ApiResponse[DigitalHumanAgentConfigInfo],
    status_code=status.HTTP_201_CREATED,
)
async def add_agent_to_digital_human(
    digital_human_id: str,
    data: AddAgentConfigRequest,
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service),
) -> ApiResponse[DigitalHumanAgentConfigInfo]:
    """为数字人添加智能体配置"""
    try:
        agent_config = service.add_agent_to_digital_human(digital_human_id, current_user.id, data)
        return ApiResponse.success(agent_config, message="添加智能体配置成功")
    except ValueError as e:
        raise BusinessException(str(e), code=ErrorCode.BUSINESS_ERROR)
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("添加智能体配置失败", e)


@router.delete(
    "/{digital_human_id}/agents/{config_id}",
    response_model=ApiResponse[None],
)
async def remove_agent_from_digital_human(
    digital_human_id: str,
    config_id: str,
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service),
) -> ApiResponse[None]:
    """从数字人移除智能体配置"""
    try:
        success = service.remove_agent_from_digital_human(digital_human_id, config_id, current_user.id)

        if not success:
            raise BusinessException(
                "智能体配置不存在或无权限删除",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return ApiResponse.success(message="移除智能体配置成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("移除智能体配置失败", e)


@router.put(
    "/{digital_human_id}/agents/{config_id}",
    response_model=ApiResponse[DigitalHumanAgentConfigInfo],
)
async def update_digital_human_agent(
    digital_human_id: str,
    config_id: str,
    data: UpdateAgentConfigRequest,
    current_user: User = Depends(get_current_user),
    service: DigitalHumanService = Depends(get_digital_human_service),
) -> ApiResponse[DigitalHumanAgentConfigInfo]:
    """更新数字人的智能体配置"""
    try:
        updated_config = service.update_digital_human_agent(
            digital_human_id=digital_human_id,
            config_id=config_id,
            user_id=current_user.id,
            data=data,
        )

        if not updated_config:
            raise BusinessException(
                "智能体配置不存在或无权限修改",
                code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND,
            )

        return ApiResponse.success(updated_config, message="更新智能体配置成功")
    except BusinessException:
        raise
    except Exception as e:
        raise _handle_unexpected_error("更新数字人智能体配置失败", e)
