## Why

The server runs only over stdio and needs Python 3.12 and `uv` on the machine that starts it. Clients cannot tell from the tool definitions that both tools only read, so they may ask for confirmation they do not need. A user who wants to run the server in a container, or reach it from another process on a trusted network, has no supported way to do so, and doing that without authentication would be unsafe.

## What Changes

- Mark both tools with the standard MCP tool annotations that state what they do: read-only, no destructive effect, repeatable with the same result for the same input, and reaching one fixed external service (the configured normkompass API).
- Add an optional streamable-HTTP transport next to stdio. It listens on the loopback address by default. It requires a bearer token whenever it listens on a non-loopback address, and the server refuses to start without one in that case. The token comes from an environment variable, is compared in constant time, and is never logged or returned.
- Add a container image that runs the server (stdio by default, HTTP when configured), as a non-root user, with no secret baked in.
- Keep stdio as the default; nothing changes for current users.

Out of scope: hosting the server publicly, TLS termination (a reverse proxy is the user's job), multiple users or per-user tokens, rate limiting, and any change to normkompass itself. normkompass has no authentication or limits of its own, so a public deployment is not supported and the README says why.

## Capabilities

### New Capabilities

- `transport`: how the server is reached (stdio, optional HTTP), the address it binds to, and the authentication it requires.
- `packaging`: the container image and how it is started.

### Modified Capabilities

- `mcp-tools`: both tools carry annotations that describe them truthfully.

## Impact

- New code for the HTTP transport and token check, a Dockerfile, tests for authentication and annotations, CI to build the image, README sections; no change for stdio users.
- Needs checking against the installed MCP SDK how the HTTP transport and its security settings are exposed; the choice is recorded at implementation.
