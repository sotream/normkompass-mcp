import hmac
import logging

import httpx
import pytest
from starlette.responses import PlainTextResponse
from starlette.types import Receive, Scope, Send

from normkompass_mcp.transport import (
    BearerTokenMiddleware,
    ConfigError,
    is_loopback,
    load_transport,
)

TOKEN = "correct-horse-battery-staple"


class TestLoadTransport:
    def test_defaults_to_stdio(self) -> None:
        config = load_transport({})
        assert config.transport == "stdio"
        assert config.host == "127.0.0.1"
        assert config.token is None

    def test_http_without_an_address_listens_on_loopback_without_a_token(self) -> None:
        config = load_transport({"NORMKOMPASS_MCP_TRANSPORT": "http"})
        assert (config.transport, config.host, config.port, config.token) == (
            "http",
            "127.0.0.1",
            8000,
            None,
        )

    @pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.5", "example.test"])
    def test_a_non_loopback_address_without_a_token_refuses_to_start(self, host: str) -> None:
        env = {"NORMKOMPASS_MCP_TRANSPORT": "http", "NORMKOMPASS_MCP_HOST": host}
        with pytest.raises(ConfigError, match="needs a bearer token"):
            load_transport(env)

    def test_a_non_loopback_address_with_a_token_is_accepted(self) -> None:
        env = {
            "NORMKOMPASS_MCP_TRANSPORT": "http",
            "NORMKOMPASS_MCP_HOST": "0.0.0.0",
            "NORMKOMPASS_MCP_TOKEN": TOKEN,
        }
        assert load_transport(env).token == TOKEN

    def test_stdio_ignores_the_host_rules(self) -> None:
        assert load_transport({"NORMKOMPASS_MCP_HOST": "0.0.0.0"}).transport == "stdio"

    def test_a_short_token_is_rejected_and_not_echoed(self) -> None:
        env = {"NORMKOMPASS_MCP_TRANSPORT": "http", "NORMKOMPASS_MCP_TOKEN": "short"}
        with pytest.raises(ConfigError, match="at least 16") as info:
            load_transport(env)
        assert "short" not in str(info.value).replace("at least 16 characters", "")

    @pytest.mark.parametrize(
        "env",
        [
            {"NORMKOMPASS_MCP_TRANSPORT": "websocket"},
            {"NORMKOMPASS_MCP_TRANSPORT": "http", "NORMKOMPASS_MCP_PORT": "abc"},
            {"NORMKOMPASS_MCP_TRANSPORT": "http", "NORMKOMPASS_MCP_PORT": "0"},
            {"NORMKOMPASS_MCP_TRANSPORT": "http", "NORMKOMPASS_MCP_PORT": "70000"},
        ],
    )
    def test_invalid_values_are_reported(self, env: dict[str, str]) -> None:
        with pytest.raises(ConfigError):
            load_transport(env)


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("127.0.0.1", True),
        ("127.5.5.5", True),
        ("::1", True),
        ("[::1]", True),
        ("localhost", True),
        ("0.0.0.0", False),
        ("192.168.1.5", False),
        ("10.0.0.1", False),
        ("example.test", False),
        ("::", False),
    ],
)
def test_is_loopback(host: str, expected: bool) -> None:
    assert is_loopback(host) is expected


async def inner(scope: Scope, receive: Receive, send: Send) -> None:
    await PlainTextResponse("inner reached")(scope, receive, send)


def client() -> httpx.AsyncClient:
    app = BearerTokenMiddleware(inner, TOKEN)
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


@pytest.mark.anyio
async def test_the_right_token_reaches_the_app() -> None:
    async with client() as http:
        response = await http.get("/", headers={"Authorization": f"Bearer {TOKEN}"})
    assert (response.status_code, response.text) == (200, "inner reached")


@pytest.mark.anyio
async def test_the_scheme_is_case_insensitive() -> None:
    async with client() as http:
        response = await http.get("/", headers={"Authorization": f"bearer {TOKEN}"})
    assert response.status_code == 200


@pytest.mark.anyio
@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Authorization": "Bearer wrong-token-of-another-length"},
        {"Authorization": f"Bearer {TOKEN}x"},
        {"Authorization": f"Basic {TOKEN}"},
        {"Authorization": "Bearer"},
        {"Authorization": "Bearer "},
        {"Authorization": TOKEN},
    ],
)
async def test_a_missing_or_wrong_token_is_rejected_before_the_app_runs(
    headers: dict[str, str],
) -> None:
    async with client() as http:
        response = await http.get("/", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert "inner reached" not in response.text
    assert TOKEN not in response.text
    assert TOKEN not in str(response.headers)


@pytest.mark.anyio
async def test_a_rejection_logs_neither_the_expected_nor_the_received_token(
    caplog: pytest.LogCaptureFixture,
) -> None:
    received = "attacker-supplied-secret-value"
    with caplog.at_level(logging.DEBUG):
        async with client() as http:
            await http.get("/", headers={"Authorization": f"Bearer {received}"})
    assert "Request rejected" in caplog.text
    assert TOKEN not in caplog.text
    assert received not in caplog.text


@pytest.mark.anyio
async def test_the_token_is_compared_in_constant_time(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[bytes, bytes]] = []
    real = hmac.compare_digest

    def spy(a: bytes, b: bytes) -> bool:
        calls.append((a, b))
        return bool(real(a, b))

    monkeypatch.setattr(hmac, "compare_digest", spy)
    async with client() as http:
        await http.get("/", headers={"Authorization": "Bearer nope"})
        await http.get("/", headers={"Authorization": f"Bearer {TOKEN}"})
    assert [a for a, _ in calls] == [b"nope", TOKEN.encode()]
