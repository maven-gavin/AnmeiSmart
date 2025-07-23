"""
用户信息MCP工具（装饰器模式）

为Dify Agent提供用户基本信息查询能力，
用于生成个性化的欢迎消息和内容。
"""
import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.services import user_service
from ..server import mcp_server

logger = logging.getLogger(__name__)


@mcp_server.tool()
async def get_user_profile(user_id: str, include_details: bool = False) -> Dict[str, Any]:
    """
    获取用户基本信息，包括用户名、邮箱、角色等，用于生成个性化内容
    
    Args:
        user_id: 用户ID
        include_details: 是否包含详细信息（头像、电话等）
    
    Returns:
        Dict: 用户信息字典，包含用户名、邮箱、角色等信息
    """
    db = next(get_db())
    
    try:
        logger.info(f"获取用户信息: user_id={user_id}, include_details={include_details}")
        
        # 通过user_service获取用户信息
        user_response = await user_service.get(db, id=user_id)
        
        if not user_response:
            logger.warning(f"用户不存在: {user_id}")
            return {
                "error": "User not found",
                "error_code": "USER_NOT_FOUND", 
                "user_id": user_id
            }
        
        # 构建基础用户信息
        user_info = {
            "user_id": user_response.id,
            "username": user_response.username,
            "email": user_response.email,
            "roles": user_response.roles,
            "is_active": user_response.is_active,
            "registration_time": user_response.created_at.isoformat() if user_response.created_at else None,
            "is_new_user": _is_new_user(user_response),
            "primary_role": _get_primary_role(user_response.roles),
            "role_display": _get_role_display_name(_get_primary_role(user_response.roles)),
            "source": "mcp_user_profile_tool"
        }
        
        # 根据请求包含详细信息
        if include_details:
            user_info.update({
                "phone": user_response.phone,
                "avatar": user_response.avatar,
                "last_updated": user_response.updated_at.isoformat() if user_response.updated_at else None
            })
        
        logger.info(f"成功获取用户信息: user_id={user_id}, primary_role={user_info['primary_role']}")
        return user_info
        
    except Exception as e:
        logger.error(f"获取用户信息失败: user_id={user_id}, error={e}", exc_info=True)
        return {
            "error": f"Failed to get user profile: {str(e)}",
            "error_code": "INTERNAL_ERROR",
            "user_id": user_id
        }
    finally:
        db.close()


def _is_new_user(user) -> bool:
    """判断是否为新用户（注册后24小时内）"""
    try:
        if not user.created_at:
            return False
        
        now = datetime.now(user.created_at.tzinfo) if user.created_at.tzinfo else datetime.now()
        return (now - user.created_at) < timedelta(hours=24)
        
    except Exception:
        return False


def _get_primary_role(roles: list) -> str:
    """获取主要角色"""
    if not roles:
        return "unknown"
    
    # 角色优先级：admin > consultant > doctor > operator > customer
    role_priority = {
        "admin": 5,
        "consultant": 4, 
        "doctor": 3,
        "operator": 2,
        "customer": 1
    }
    
    # 找到优先级最高的角色
    primary_role = max(roles, key=lambda role: role_priority.get(role, 0))
    return primary_role


def _get_role_display_name(role: str) -> str:
    """获取角色显示名称"""
    role_names = {
        "admin": "系统管理员",
        "consultant": "美容顾问", 
        "doctor": "医美医生",
        "operator": "运营人员",
        "customer": "客户",
        "unknown": "未知角色"
    }
    return role_names.get(role, role) 