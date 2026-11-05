import httpx
import pytest

from normkompass_mcp.client import AskNotConfigured, ClientError, NormkompassClient

from .conftest import ANSWER, StubApi, passage

BASE = "http://api.test"


def make(stub: StubApi) -> NormkompassClient:
    return NormkompassClient(BASE, transport=stub.transport)


@pytest.mark.anyio
async def test_search_sends_question_and_limit_and_keeps_order(stub: StubApi) -> None:
    stub.respond("/search", {"results": [passage("B"), passage("A")]})
    passages = await make(stub).search("Frage", 7)
    assert stub.body() == {"question": "Frage", "limit": 7}
    assert [p.label for p in passages] == ["B", "A"]


@pytest.mark.anyio
async def test_ask_parses_answer(stub: StubApi) -> None:
    stub.respond("/ask", ANSWER)
    response = await make(stub).ask("Frage")
    assert stub.body() == {"question": "Frage"}
    assert response.citations[0].quote == "nicht mehr als 6.000 Kilometer zurückgelegt hat"


@pytest.mark.anyio
async def test_bad_request_message_is_passed_on(stub: StubApi) -> None:
    stub.respond("/search", {"message": '"limit" must be an integer between 1 and 20'}, 400)
    with pytest.raises(ClientError, match="limit"):
        await make(stub).search("Frage", 5)


@pytest.mark.anyio
async def test_ask_503_means_not_configured(stub: StubApi) -> None:
    stub.respond("/ask", {"message": "no model"}, 503)
    with pytest.raises(AskNotConfigured, match="search_law still works"):
        await make(stub).ask("Frage")


@pytest.mark.anyio
async def test_search_503_is_an_unexpected_status(stub: StubApi) -> None:
    stub.respond("/search", {}, 503)
    with pytest.raises(ClientError, match="unexpected status 503") as info:
        await make(stub).search("Frage", 5)
    assert not isinstance(info.value, AskNotConfigured)


@pytest.mark.anyio
async def test_unreachable_names_the_address(stub: StubApi) -> None:
    def refuse(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused")

    stub.route("/search", refuse)
    with pytest.raises(ClientError, match=r"http://api\.test is not reachable"):
        await make(stub).search("Frage", 5)


@pytest.mark.anyio
async def test_timeout_is_reported_and_not_retried(stub: StubApi) -> None:
    def slow(_request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow")

    stub.route("/ask", slow)
    with pytest.raises(ClientError, match="did not answer within"):
        await make(stub).ask("Frage")
    assert len(stub.requests) == 1


@pytest.mark.anyio
@pytest.mark.parametrize("body", [{}, {"results": "x"}, {"results": [{"label": "A"}]}, []])
async def test_malformed_search_response_is_an_error_not_an_empty_list(
    stub: StubApi, body: object
) -> None:
    stub.respond("/search", body)
    with pytest.raises(ClientError, match="unexpected shape"):
        await make(stub).search("Frage", 5)


@pytest.mark.anyio
async def test_non_json_response_is_an_error(stub: StubApi) -> None:
    stub.route("/ask", lambda _r: httpx.Response(200, text="<html>"))
    with pytest.raises(ClientError, match="not JSON"):
        await make(stub).ask("Frage")
