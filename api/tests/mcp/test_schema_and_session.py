import asyncio
import pytest
from app.mcp.registry.tool_registry import MCPToolRegistry
from app.mcp.session_manager import issue_session_token, validate_session_token, revoke_session_token


async def sample_tool(a: int, b: str = "x", flag: bool = False):
    return {"a": a, "b": b, "flag": flag}


def test_build_input_schema_from_signature():
    registry = MCPToolRegistry()
    registry.register_tool("sample", sample_tool, description="", category="test")
    schema = registry.build_input_schema("sample")
    assert schema["type"] == "object"
    assert set(schema["properties"].keys()) == {"a", "b", "flag"}
    assert "a" in schema["required"]
    assert schema["properties"]["b"]["default"] == "x"
    assert schema["properties"]["flag"]["type"] in {"boolean", "bool"}


@pytest.mark.asyncio
async def test_session_manager_issue_validate_revoke(monkeypatch):
    # 使用内存假的 Redis 客户端
    class DummyRedis:
        def __init__(self):
            self.store = {}
        async def set(self, k, v, ex=None):
            self.store[k] = v
        async def get(self, k):
            return self.store.get(k)
        async def delete(self, k):
            self.store.pop(k, None)

    from app.core import redis_client as rc
    dummy = DummyRedis()
    async def get_client():
        return dummy
    monkeypatch.setattr(rc, "get_redis_client", get_client)

    token = await issue_session_token({"id": "g1", "name": "G"}, client_name="test", allowed_tools=["t1"])  # type: ignore
    data = await validate_session_token(token)
    assert data and data.get("group_id") == "g1"
    await revoke_session_token(token)
    data2 = await validate_session_token(token)
    assert data2 is None


