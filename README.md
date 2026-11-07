# normkompass-mcp

A small [MCP](https://modelcontextprotocol.io) server in Python that lets an AI agent search German federal law
and ask cited questions through [normkompass](https://github.com/sotream/normkompass), a TypeScript RAG service
that answers only with verifiable citations and refuses when the corpus does not support an answer.

**Status:** reference implementation, version 0.1.0. It is a thin client: it adds no retrieval, no model and no
storage. Not legal advice.

## Tools

| Tool         | Input                                                           | Result                                                                                                                                          |
| ------------ | --------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `search_law` | `question` (1 to 1000 characters), `limit` (1 to 20, default 5) | Ranked passages in the API's order: source law, citation label (for example "§ 1b Abs. 3 UStG"), title, URL, Stand, text.                       |
| `ask_law`    | `question` (1 to 1000 characters)                               | `refused: false` with the answer, its citations (source, path, URL, quote) and the Stand, or `refused: true` with a message and no answer text. |

- **Refusal is a normal result, not an error.** When normkompass finds no answer that its citation check
  supports, the agent gets `refused: true`. The quote checking (every quote a verbatim part of a retrieved
  passage) happens in normkompass; this server passes the citations through exactly as returned and discards an
  answer that comes without one.
- **Errors are short tool errors**: invalid input (nothing is sent to the API), API not reachable (names the
  configured address), timeout (30 s for search, 120 s for ask, no silent retry), a response in an unexpected
  shape, and an API without an answer model (`ask_law` fails, `search_law` still works).
- The server starts and lists its tools even when the API is down; the failure shows when a tool is called.

## Requirements

- A running normkompass API (see its [README](https://github.com/sotream/normkompass#quick-start); default
  address `http://localhost:3000`). `ask_law` additionally needs an answer model configured there.
- Python 3.12 or newer and [uv](https://docs.astral.sh/uv/).

Set `NORMKOMPASS_API_URL` if the API is elsewhere (see `.env.example`). No secrets are read or stored. The server
sends requests only to that address; what normkompass does with a question (for example sending it to a hosted
answer model) is described in its README.

## Connect it to an MCP client

The server speaks MCP over stdio. The command is the same for every client:

```sh
uv run --directory /path/to/normkompass-mcp normkompass-mcp
```

Claude Code:

```sh
claude mcp add normkompass -e NORMKOMPASS_API_URL=http://localhost:3000 -- \
  uv run --directory /path/to/normkompass-mcp normkompass-mcp
```

A client configured through JSON (for example Claude Desktop) takes the same command in its `mcpServers` entry:

```json
{
  "mcpServers": {
    "normkompass": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/normkompass-mcp", "normkompass-mcp"],
      "env": { "NORMKOMPASS_API_URL": "http://localhost:3000" }
    }
  }
}
```

### What has been run

On 2026-11-05 the server was started with that command (`uv run normkompass-mcp`) by the MCP Python SDK's
client over stdio against a live normkompass API with the default search and the answer model
`gemini-3.5-flash-lite` (free hosted tier, a third party). The client listed the two tools; `search_law` returned
`§ 18 Abs. 10 UStG` and `§ 1b Abs. 3 UStG` for "Wann gilt ein Landfahrzeug als neu?"; `ask_law` answered that
question with the citation `§ 1b Abs. 3` and refused "Wie hoch ist der gesetzliche Mindestlohn pro Stunde?".

On 2026-11-07 the Docker image was run against a live normkompass API (answer model `gemini-3.5-flash-lite`, free
hosted tier). Over stdio (`docker run -i`) the tools were listed with their annotations and `search_law`
returned `§ 18 Abs. 10 UStG` and `§ 1b Abs. 3 UStG`. Over HTTP with a token, a request without a token and one
with a wrong token got `401`, the right token got `200`, and `ask_law` answered "Wann gilt ein Landfahrzeug als
neu?" with the citation `§ 1b Abs. 3`. The container log contained the rejections but not the token.

**Not run:** the two client snippets above were not run in Claude Code or Claude Desktop themselves. They use the
documented configuration shape with the command that was run. If a client rejects them, that is a bug in this
page; please open an issue.

## Annotations

Both tools are annotated as read-only, not destructive and idempotent, and as contacting one fixed service (the
configured normkompass API). These are hints for clients, as the MCP specification says, not a security control.

## HTTP transport

stdio is the default and is unchanged. For a process that cannot start the server itself, an optional streamable
HTTP transport is available:

```sh
NORMKOMPASS_MCP_TRANSPORT=http uv run normkompass-mcp          # http://127.0.0.1:8000/mcp
```

| Variable                    | Meaning                                                                    |
| --------------------------- | -------------------------------------------------------------------------- |
| `NORMKOMPASS_MCP_TRANSPORT` | `stdio` (default) or `http`                                                |
| `NORMKOMPASS_MCP_HOST`      | address to listen on, default `127.0.0.1`                                  |
| `NORMKOMPASS_MCP_PORT`      | port, default `8000`                                                       |
| `NORMKOMPASS_MCP_TOKEN`     | bearer token, at least 16 characters; **required** on a non-loopback host |

On a loopback address the token is optional. On any other address the server refuses to start without one, and
every request must carry `Authorization: Bearer <token>`; others get `401` before any tool runs. The token is
compared in constant time and is never logged or returned, and a rejected request is logged without either the
expected or the received value.

**Limits you should know.** The server does not terminate TLS, so a bearer token over plain HTTP can be read by
anyone on the network path: put a reverse proxy with TLS in front, or stay on loopback. **A public deployment is
not supported.** The normkompass API behind this server has no authentication and no rate limits, and it may
forward questions to a hosted answer model, so exposing the server would hand that capability, and its cost, to
whoever can reach it. There is one token for all users, no per-user control and no rate limiting here either.

## Container

```sh
docker build -t normkompass-mcp .

# stdio (the client starts the container; -i keeps stdin open)
docker run -i --rm -e NORMKOMPASS_API_URL=http://host.docker.internal:3000 normkompass-mcp

# HTTP with a token (the token is read from your environment, not baked into the image)
docker run --rm -p 127.0.0.1:8000:8000 \
  -e NORMKOMPASS_MCP_TRANSPORT=http -e NORMKOMPASS_MCP_HOST=0.0.0.0 \
  -e NORMKOMPASS_MCP_TOKEN="$TOKEN" -e NORMKOMPASS_API_URL=http://host.docker.internal:3000 \
  normkompass-mcp
```

The image runs as a non-root user and contains no secret; the API address and the token are given at run time.
`host.docker.internal` reaches an API on the host on Docker Desktop; elsewhere use an address the container can
reach. Binding to `0.0.0.0` inside the container is safe only because the token is mandatory and the port is
published to `127.0.0.1`.

## Development

```sh
uv sync
uv run ruff format --check . && uv run ruff check . && uv run mypy && uv run pytest
```

Tests run against a stub of the normkompass API (71 tests, no corpus, database or model needed), including a test
that starts the server as a subprocess over stdio. CI runs the same checks plus `openspec validate --strict`.
Work follows [OpenSpec](https://github.com/Fission-AI/OpenSpec): the specification in `openspec/` was merged as a
separate pull request before any code.

## Limits

- Answer quality is that of normkompass and its model; nothing about quality is measured here. See the
  normkompass README ("Honest limits") for what is known, in particular that Claude has not been measured there.
- No TLS, no per-user tokens, no rate limiting, no caching, and no public hosting (see "HTTP transport").
- One corpus (five German federal laws, a snapshot with the Stand shown per result). No promise that the law
  shown is current or complete.

## License

MIT, see [LICENSE](LICENSE).
