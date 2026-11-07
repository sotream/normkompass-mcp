# Runs the MCP server. Nothing secret is baked in: the API address and any token are given at run time.
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS build
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
COPY pyproject.toml uv.lock README.md LICENSE ./
COPY src ./src
RUN uv sync --locked --no-dev --no-editable

FROM python:3.12-slim-bookworm
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin mcp
COPY --from=build /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1
USER mcp
# stdio is the default (run with -i); set NORMKOMPASS_MCP_TRANSPORT=http and publish the port for HTTP.
ENTRYPOINT ["normkompass-mcp"]
