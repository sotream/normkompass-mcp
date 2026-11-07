"""The tools, exercised through the MCP protocol against the stub API."""

from typing import Any

import httpx
import pytest
from mcp import Client

from normkompass_mcp.client import NormkompassClient
from normkompass_mcp.server import build_server

from .conftest import ANSWER, REFUSED, StubApi, passage


def connect(stub: StubApi) -> Client:
    return Client(build_server(NormkompassClient("http://api.test", transport=stub.transport)))


def text_of(result: Any) -> str:
    return str(result.content[0].text)


@pytest.mark.anyio
async def test_lists_exactly_two_tools_with_descriptions(stub: StubApi) -> None:
    async with connect(stub) as client:
        tools = (await client.list_tools()).tools
    assert sorted(t.name for t in tools) == ["ask_law", "search_law"]
    for tool in tools:
        assert tool.description is not None
        assert "German federal law" in tool.description
        assert "Not legal advice" in tool.description
        assert "Stand" in tool.description
    assert stub.requests == []


@pytest.mark.anyio
async def test_both_tools_are_annotated_read_only_non_destructive_and_idempotent(
    stub: StubApi,
) -> None:
    async with connect(stub) as client:
        tools = (await client.list_tools()).tools
    for tool in tools:
        assert tool.annotations is not None
        assert tool.annotations.read_only_hint is True
        assert tool.annotations.destructive_hint is False
        assert tool.annotations.idempotent_hint is True
        assert tool.annotations.open_world_hint is False


@pytest.mark.anyio
async def test_starts_and_lists_tools_when_the_api_is_down() -> None:
    def down(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return down(request)

    server = build_server(
        NormkompassClient("http://api.test", transport=httpx.MockTransport(handler))
    )
    async with Client(server) as client:
        assert len((await client.list_tools()).tools) == 2
    assert seen == []


@pytest.mark.anyio
async def test_search_returns_passages_in_api_order(stub: StubApi) -> None:
    stub.respond("/search", {"results": [passage("§ 14 Abs. 2 UStG"), passage("§ 14 Abs. 1 UStG")]})
    async with connect(stub) as client:
        result = await client.call_tool("search_law", {"question": "Rechnung", "limit": 2})
    assert not result.is_error
    passages = result.structured_content["passages"]
    assert [p["label"] for p in passages] == ["§ 14 Abs. 2 UStG", "§ 14 Abs. 1 UStG"]
    assert set(passages[0]) == {"source", "label", "title", "url", "stand", "text"}
    assert stub.body() == {"question": "Rechnung", "limit": 2}


@pytest.mark.anyio
async def test_search_uses_default_limit_and_trims_the_question(stub: StubApi) -> None:
    stub.respond("/search", {"results": []})
    async with connect(stub) as client:
        result = await client.call_tool("search_law", {"question": "  Rechnung  "})
    assert not result.is_error
    assert stub.body() == {"question": "Rechnung", "limit": 5}
    assert result.structured_content["passages"] == []


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("arguments", "field"),
    [
        ({"question": ""}, "question"),
        ({"question": "   "}, "question"),
        ({"question": "x" * 1001}, "question"),
        ({"question": "ok", "limit": 0}, "limit"),
        ({"question": "ok", "limit": 21}, "limit"),
    ],
)
async def test_invalid_search_input_is_an_error_and_sends_nothing(
    stub: StubApi, arguments: dict[str, Any], field: str
) -> None:
    async with connect(stub) as client:
        result = await client.call_tool("search_law", arguments)
    assert result.is_error
    assert f'"{field}"' in text_of(result)
    assert stub.requests == []


@pytest.mark.anyio
@pytest.mark.parametrize("question", ["", "  ", "x" * 1001])
async def test_invalid_ask_input_is_an_error_and_sends_nothing(
    stub: StubApi, question: str
) -> None:
    async with connect(stub) as client:
        result = await client.call_tool("ask_law", {"question": question})
    assert result.is_error
    assert '"question"' in text_of(result)
    assert stub.requests == []


@pytest.mark.anyio
async def test_ask_returns_the_answer_and_exactly_the_citations_of_the_api(
    stub: StubApi,
) -> None:
    stub.respond("/ask", ANSWER)
    async with connect(stub) as client:
        result = await client.call_tool("ask_law", {"question": "Wann ist ein Landfahrzeug neu?"})
    assert not result.is_error
    data = result.structured_content
    assert data["refused"] is False
    assert data["answer"] == ANSWER["answer"]
    assert data["citations"] == ANSWER["citations"]
    assert data["stand"] == ANSWER["stand"]


@pytest.mark.anyio
async def test_refusal_is_a_normal_result_without_answer_text(stub: StubApi) -> None:
    stub.respond("/ask", REFUSED)
    async with connect(stub) as client:
        result = await client.call_tool("ask_law", {"question": "Mindestlohn?"})
    assert not result.is_error
    data = result.structured_content
    assert data["refused"] is True
    assert data["answer"] == ""
    assert data["citations"] == []
    assert "no answer" in str(data["message"])


@pytest.mark.anyio
async def test_an_answer_without_citation_is_discarded(stub: StubApi) -> None:
    stub.respond("/ask", {**ANSWER, "citations": []})
    async with connect(stub) as client:
        result = await client.call_tool("ask_law", {"question": "Frage"})
    assert result.is_error
    assert "discarded" in text_of(result)
    assert str(ANSWER["answer"]) not in text_of(result)


@pytest.mark.anyio
async def test_answer_model_not_configured_says_so_and_points_to_search(stub: StubApi) -> None:
    stub.respond("/ask", {"message": "no model"}, 503)
    async with connect(stub) as client:
        result = await client.call_tool("ask_law", {"question": "Frage"})
    assert result.is_error
    message = text_of(result)
    assert "not configured" in message
    assert "search_law still works" in message


@pytest.mark.anyio
async def test_unreachable_api_error_names_the_address_and_has_no_trace(stub: StubApi) -> None:
    def refuse(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    stub.route("/search", refuse)
    async with connect(stub) as client:
        result = await client.call_tool("search_law", {"question": "Frage"})
    assert result.is_error
    message = text_of(result)
    assert "http://api.test is not reachable" in message
    assert "Traceback" not in message
