"""
用户搜索MCP工具

提供用户搜索功能
"""

from app.mcp.registry import mcp_tool


@mcp_tool(
    name="search_users",
    description="搜索系统用户，支持按用户名、邮箱等条件搜索",
    category="user"
)
async def search_users(query: str, limit: int = 10) -> list:
    """
    搜索用户
    
    Args:
        query: 搜索关键词
        limit: 返回结果数量限制
    
    Returns:
        List: 用户搜索结果列表
    """
    # TODO: 实现真实的用户搜索逻辑
    # 实际实现时应该：
    # 1. 使用数据库模糊查询
    # 2. 支持按用户名、邮箱、角色等字段搜索
    # 3. 实现分页和排序
    # 4. 添加权限检查，确保只能搜索有权限查看的用户
    
    return [
        {
            "user_id": f"user_{i}",
            "username": f"用户_{i}",
            "email": f"user{i}@example.com",
            "roles": ["customer"],
            "match_score": 0.9 - (i * 0.1)
        }
        for i in range(min(limit, 3))
    ] 