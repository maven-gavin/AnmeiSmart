"""
咨询总结MCP工具
"""

import secrets
from datetime import datetime
from app.mcp.registry import mcp_tool


@mcp_tool(
    name="create_consultation_summary",
    description="创建咨询总结和记录",
    category="consultation"
)
async def create_consultation_summary(consultation_data: dict) -> dict:
    """创建咨询总结"""
    # TODO: 实现真实的咨询总结创建逻辑
    return {
        "summary_id": f"summary_{secrets.token_urlsafe(8)}",
        "created_at": datetime.now().isoformat(),
        "status": "已创建",
        "consultation_type": consultation_data.get("type", "常规咨询"),
        "key_points": ["客户需求明确", "方案建议已提供"]
    } 