"""How the server is reached: stdio by default, optional streamable HTTP and its rules."""

import hmac
import ipaddress
import logging
import os
from dataclasses import dataclass
from typing import Literal

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

ENV_TRANSPORT = "NORMKOMPASS_MCP_TRANSPORT"
ENV_HOST = "NORMKOMPASS_MCP_HOST"
ENV_PORT = "NORMKOMPASS_MCP_PORT"
ENV_TOKEN = "NORMKOMPASS_MCP_TOKEN"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
MIN_TOKEN_LENGTH = 16

logger = logging.getLogger("normkompass_mcp.transport")


class ConfigError(Exception):
    """The transport configuration is not acceptable; the message says what to change."""


@dataclass(frozen=True)
class TransportConfig:
    transport: Literal["stdio", "http"]
    host: str
    port: int
    token: str | None


def is_loopback(host: str) -> bool:
    """True for localhost and for loopback IP addresses; any other name or address is not."""
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host.strip("[]")).is_loopback
    except ValueError:
        return False


def load_transport(env: dict[str, str] | None = None) -> TransportConfig:
    """Read and check the transport configuration; ConfigError when it is not safe or valid."""
    values = os.environ if env is None else env
    transport = values.get(ENV_TRANSPORT, "").strip().lower() or "stdio"
    if transport not in ("stdio", "http"):
        raise ConfigError(f'{ENV_TRANSPORT} must be "stdio" or "http", not "{transport}".')
    host = values.get(ENV_HOST, "").strip() or DEFAULT_HOST
    raw_port = values.get(ENV_PORT, "").strip() or str(DEFAULT_PORT)
    try:
        port = int(raw_port)
    except ValueError:
        raise ConfigError(f"{ENV_PORT} must be a number between 1 and 65535.") from None
    if not 1 <= port <= 65535:
        raise ConfigError(f"{ENV_PORT} must be a number between 1 and 65535.")
    token = values.get(ENV_TOKEN, "").strip() or None

    if transport == "http":
        if token is not None and len(token) < MIN_TOKEN_LENGTH:
            raise ConfigError(f"{ENV_TOKEN} must have at least {MIN_TOKEN_LENGTH} characters.")
        if not is_loopback(host) and token is None:
            raise ConfigError(
                f"Listening on {host} needs a bearer token: set {ENV_TOKEN} "
                f"(at least {MIN_TOKEN_LENGTH} characters), or listen on 127.0.0.1."
            )
    return TransportConfig(
        transport="http" if transport == "http" else "stdio", host=host, port=port, token=token
    )


class BearerTokenMiddleware:
    """Rejects HTTP requests that do not carry the expected bearer token, before anything else runs.

    The comparison takes the same time whatever the received value is, and neither the
    expected nor the received token is logged or returned.
    """

    def __init__(self, app: ASGIApp, token: str) -> None:
        self._app = app
        self._token = token.encode()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        received = _bearer(dict(scope["headers"]).get(b"authorization", b""))
        if received is None or not hmac.compare_digest(received, self._token):
            logger.warning("Request rejected: missing or invalid bearer token")
            response = JSONResponse(
                {"error": "unauthorized"},
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
            )
            await response(scope, receive, send)
            return
        await self._app(scope, receive, send)


def _bearer(header: bytes) -> bytes | None:
    scheme, _, value = header.partition(b" ")
    if scheme.lower() != b"bearer" or not value.strip():
        return None
    return value.strip()
