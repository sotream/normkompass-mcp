"""Start the server the way an MCP client does, as a subprocess over stdio."""

import sys

import pytest
from mcp import Client, StdioServerParameters


@pytest.mark.anyio
async def test_subprocess_lists_the_tools_even_when_the_api_is_down() -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "normkompass_mcp"],
        # Nothing listens here: the server must start anyway and report the failure only on a call.
        env={"NORMKOMPASS_API_URL": "http://127.0.0.1:9"},
    )
    async with Client(params) as client:
        names = sorted(tool.name for tool in (await client.list_tools()).tools)
        assert names == ["ask_law", "search_law"]
        result = await client.call_tool("search_law", {"question": "Rechnung"})
    assert result.is_error
    assert "http://127.0.0.1:9 is not reachable" in str(result.content[0].text)  # type: ignore[union-attr]
