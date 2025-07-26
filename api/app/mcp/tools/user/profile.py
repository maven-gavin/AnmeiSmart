"""
用户档案MCP工具

提供用户基本信息查询功能
"""

from app.mcp.registry import mcp_tool


@mcp_tool(
    name="get_user_profile",
    description="获取用户基本信息和档案，用于生成个性化内容",
    category="user"
)
async def get_user_profile(user_id: str, include_details: bool = False) -> dict:
    """
    获取用户基本信息
    
    Args:
        user_id: 用户ID
        include_details: 是否包含详细信息（头像、电话等）
    
    Returns:
        Dict: 用户信息字典，包含用户名、邮箱、角色等信息
    """
    # TODO: 从数据库获取真实用户信息
    # 这里使用模拟数据，实际实现时应该：
    # 1. 通过user_service.get获取用户信息
    # 2. 检查用户是否存在
    # 3. 根据include_details参数返回不同级别的信息
    
    return {
        "user_id": user_id,
        "username": f"用户_{user_id[-4:]}",
        "roles": ["customer"],
        "is_active": True,
        "registration_time": "2025-01-01T00:00:00Z",
        "details_included": include_details,
        # 如果include_details为True，可以包含更多信息
        **({"phone": "138****8888", "avatar": "/default-avatar.png"} if include_details else {})
    } 