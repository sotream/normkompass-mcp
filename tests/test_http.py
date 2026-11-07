"""The HTTP transport as a real process: authentication at the boundary."""

import socket
import subprocess
import sys
import time
from collections.abc import Iterator

import httpx
import pytest

TOKEN = "an-http-test-token-0123456789"
INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "0"},
    },
}
HEADERS = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port: int = s.getsockname()[1]
        return port


def start(env_extra: dict[str, str]) -> tuple[subprocess.Popen[bytes], int]:
    port = free_port()
    env = {
        "NORMKOMPASS_MCP_TRANSPORT": "http",
        "NORMKOMPASS_MCP_PORT": str(port),
        "NORMKOMPASS_API_URL": "http://127.0.0.1:9",
        **env_extra,
    }
    process = subprocess.Popen(
        [sys.executable, "-m", "normkompass_mcp"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("the server exited during start")
        try:
            socket.create_connection(("127.0.0.1", port), timeout=0.2).close()
            return process, port
        except OSError:
            time.sleep(0.1)
    process.kill()
    raise RuntimeError("the server did not start")


@pytest.fixture
def secured() -> Iterator[int]:
    process, port = start({"NORMKOMPASS_MCP_TOKEN": TOKEN})
    yield port
    process.terminate()
    process.wait(timeout=10)


@pytest.fixture
def open_loopback() -> Iterator[int]:
    process, port = start({})
    yield port
    process.terminate()
    process.wait(timeout=10)


def test_requests_without_or_with_a_wrong_token_are_rejected(secured: int) -> None:
    url = f"http://127.0.0.1:{secured}/mcp"
    assert httpx.post(url, json=INITIALIZE, headers=HEADERS).status_code == 401
    wrong = {**HEADERS, "Authorization": "Bearer not-the-right-token"}
    response = httpx.post(url, json=INITIALIZE, headers=wrong)
    assert response.status_code == 401
    assert TOKEN not in response.text


def test_the_right_token_reaches_the_mcp_endpoint(secured: int) -> None:
    url = f"http://127.0.0.1:{secured}/mcp"
    response = httpx.post(
        url, json=INITIALIZE, headers={**HEADERS, "Authorization": f"Bearer {TOKEN}"}
    )
    assert response.status_code == 200
    assert "normkompass" in response.text


def test_loopback_needs_no_token_when_none_is_configured(open_loopback: int) -> None:
    url = f"http://127.0.0.1:{open_loopback}/mcp"
    assert httpx.post(url, json=INITIALIZE, headers=HEADERS).status_code == 200


def test_the_server_refuses_to_start_on_an_open_address_without_a_token() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "normkompass_mcp"],
        env={
            "NORMKOMPASS_MCP_TRANSPORT": "http",
            "NORMKOMPASS_MCP_HOST": "0.0.0.0",
        },
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert result.returncode == 2
    assert b"needs a bearer token" in result.stderr
