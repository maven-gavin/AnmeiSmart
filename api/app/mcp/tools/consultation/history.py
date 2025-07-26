"""
咨询历史MCP工具
"""

from app.mcp.registry import mcp_tool


@mcp_tool(
    name="get_consultation_history",
    description="获取客户的咨询历史记录",
    category="consultation"
)
async def get_consultation_history(customer_id: str, limit: int = 10) -> list:
    """获取咨询历史"""
    # TODO: 实现真实的咨询历史查询
    return [
        {
            "consultation_id": f"cons_{i}",
            "date": "2025-01-01",
            "type": "初次咨询",
            "summary": "客户咨询面部护理方案",
            "consultant": f"顾问_{i}",
            "status": "已完成"
        }
        for i in range(min(limit, 2))
    ] 