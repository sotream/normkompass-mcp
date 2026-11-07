## Context

The server is a thin client of the normkompass HTTP API, which has no authentication and no rate limits and forwards questions to a configured answer model that may be a third-party service. An MCP server reachable over a network would hand that capability, and its cost, to whoever can reach it.

## Decisions

- **Annotations state facts.** Read-only: true, destructive: false, idempotent: true (same input, same result barring corpus changes), open world: false in the sense that the server contacts one configured address. They are hints for clients, not security controls.
- **HTTP is opt-in and local by default.** Stdio stays the default. The HTTP transport binds to 127.0.0.1 unless told otherwise.
- **Authentication tied to the bind address.** On a non-loopback address a bearer token is mandatory and the process exits with a clear message when none is set. On loopback the token is optional, because other local processes of the same user are already trusted by stdio.
- **Token handling.** The token is read from one environment variable, compared with a constant-time comparison, never written to logs, error messages or tool results, and a request without or with a wrong token is rejected before any tool runs, with no hint about the expected value.
- **No TLS in the server.** Put a reverse proxy in front for TLS; the README says so and does not claim transport security the server does not provide.
- **Container.** A small image, non-root user, no secrets in layers or in the image configuration, the API address and token given at run time. Stdio inside a container needs an interactive attachment, so the README documents that and the HTTP mode for the common case.
- **Not a public service.** Because normkompass behind it has no authentication or limits, the README states that exposing the server publicly is unsupported.

## Risks

- Annotations can be read as guarantees; the tool descriptions and README call them hints.
- A bearer token over plain HTTP is readable on the network; hence loopback by default and the proxy advice.
- The SDK's HTTP and security settings may change; the version is pinned and the use is tested.
