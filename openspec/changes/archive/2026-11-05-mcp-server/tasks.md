## 1. Package and tooling

- [x] 1.1 Create the Python package with a pinned MCP SDK and an HTTP client, the lint, type-check and test setup, and a CI workflow that runs them and `openspec validate --strict`
- [x] 1.2 Add `.env.example` with `NORMKOMPASS_API_URL` and no secrets

## 2. Client

- [x] 2.1 Implement the normkompass client for search and ask with timeouts and the failure mapping
- [x] 2.2 Test it against a stub of the API, including 400, 503, an unreachable host and a timeout

## 3. Tools

- [x] 3.1 Implement `search_law` with input checks and the result shape
- [x] 3.2 Implement `ask_law` with refusal shown as a result and the error cases
- [x] 3.3 Test both tools through the MCP protocol (list tools, call tools) against the stub

## 4. Docs and wrap-up

- [x] 4.1 Write the README: what it is, status, the connection snippets for an MCP client, and a manual end-to-end run against a live normkompass with its date and the model used
- [x] 4.2 Run `openspec archive mcp-server` and keep the Purpose sections filled
