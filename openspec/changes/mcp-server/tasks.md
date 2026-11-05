## 1. Package and tooling

- [ ] 1.1 Create the Python package with a pinned MCP SDK and an HTTP client, the lint, type-check and test setup, and a CI workflow that runs them and `openspec validate --strict`
- [ ] 1.2 Add `.env.example` with `NORMKOMPASS_API_URL` and no secrets

## 2. Client

- [ ] 2.1 Implement the normkompass client for search and ask with timeouts and the failure mapping
- [ ] 2.2 Test it against a stub of the API, including 400, 503, an unreachable host and a timeout

## 3. Tools

- [ ] 3.1 Implement `search_law` with input checks and the result shape
- [ ] 3.2 Implement `ask_law` with refusal shown as a result and the error cases
- [ ] 3.3 Test both tools through the MCP protocol (list tools, call tools) against the stub

## 4. Docs and wrap-up

- [ ] 4.1 Write the README: what it is, status, the connection snippets for an MCP client, and a manual end-to-end run against a live normkompass with its date and the model used
- [ ] 4.2 Run `openspec archive mcp-server` and keep the Purpose sections filled
