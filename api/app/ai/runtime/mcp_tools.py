"""将 MCP 工具组暴露为 LangChain Tool。"""

from __future__ import annotations

import json
import logging
from typing import Any, List

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field, create_model
from sqlalchemy.orm import Session

from app.mcp.models.mcp import MCPTool, MCPToolGroup
from app.mcp.services.mcp_service import MCPToolExecutionService

logger = logging.getLogger(__name__)


def _schema_to_pydantic(tool_name: str, schema: dict[str, Any]) -> type[BaseModel]:
    props = schema.get("properties") or {}
    required = set(schema.get("required") or [])
    fields: dict[str, Any] = {}
    for name, spec in props.items():
        py_type = str
        if spec.get("type") == "integer":
            py_type = int
        elif spec.get("type") == "number":
            py_type = float
        elif spec.get("type") == "boolean":
            py_type = bool
        if name in required:
            fields[name] = (py_type, Field(description=spec.get("description", "")))
        else:
            fields[name] = (py_type | None, Field(default=None, description=spec.get("description", "")))
    if not fields:
        fields["_placeholder"] = (str | None, Field(default=None))
    return create_model(f"MCP_{tool_name}_Args", **fields)


def build_mcp_tools_for_groups(db: Session, group_names: List[str]) -> list[StructuredTool]:
    tools: list[StructuredTool] = []
    execution = MCPToolExecutionService(db)

    for group_name in group_names:
        group = (
            db.query(MCPToolGroup)
            .filter(MCPToolGroup.name == group_name, MCPToolGroup.enabled.is_(True))
            .first()
        )
        if not group or not group.server_code:
            logger.warning("MCP 工具组不可用: %s", group_name)
            continue

        mcp_tools = (
            db.query(MCPTool)
            .filter(MCPTool.group_id == group.id, MCPTool.enabled.is_(True))
            .all()
        )
        for mcp_tool in mcp_tools:
            tools.append(_wrap_mcp_tool(db, execution, group.server_code, mcp_tool))

    return tools


def _wrap_mcp_tool(
    db: Session,
    execution: MCPToolExecutionService,
    server_code: str,
    mcp_tool: MCPTool,
) -> StructuredTool:
    schema = (mcp_tool.config_data or {}).get("inputSchema") or {
        "type": "object",
        "properties": {},
    }
    args_model = _schema_to_pydantic(mcp_tool.tool_name, schema)
    tool_name = mcp_tool.tool_name
    description = mcp_tool.description or f"MCP 工具 {tool_name}"

    async def _run(**kwargs: Any) -> str:
        kwargs.pop("_placeholder", None)
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        result = await execution.execute_tool(
            server_code=server_code,
            tool_name=tool_name,
            arguments=kwargs,
            caller_app_id="langgraph_agent",
        )
        content = result.get("content") if isinstance(result, dict) else result
        if isinstance(content, list):
            texts = [c.get("text", "") for c in content if isinstance(c, dict)]
            return "\n".join(texts) or json.dumps(result, ensure_ascii=False)
        return str(content or result)

    return StructuredTool.from_function(
        coroutine=_run,
        name=tool_name,
        description=description,
        args_schema=args_model,
    )
