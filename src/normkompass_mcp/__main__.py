"""Entry point: stdio by default, streamable HTTP when NORMKOMPASS_MCP_TRANSPORT=http."""

import sys

import uvicorn
from starlette.types import ASGIApp

from .server import build_server
from .transport import BearerTokenMiddleware, ConfigError, TransportConfig, load_transport


def make_http_app(config: TransportConfig) -> ASGIApp:
    """The ASGI app of the HTTP transport, behind the bearer token check when a token is set."""
    app = build_server().streamable_http_app(host=config.host)
    return BearerTokenMiddleware(app, config.token) if config.token else app


def main() -> None:
    try:
        config = load_transport()
    except ConfigError as error:
        print(f"normkompass-mcp: {error}", file=sys.stderr)
        raise SystemExit(2) from None
    if config.transport == "stdio":
        build_server().run("stdio")
    else:
        uvicorn.run(make_http_app(config), host=config.host, port=config.port, log_level="info")


if __name__ == "__main__":
    main()
