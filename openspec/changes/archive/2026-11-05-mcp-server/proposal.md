## Why

normkompass answers questions over German federal law with exact citations, but only through its own HTTP API. An AI agent (an MCP-capable client such as an IDE assistant or a desktop chat app) cannot use it unless someone wraps it as a tool. A small MCP server in Python makes the search and the cited answers available to any such agent and is a concrete example of tool calling against a service whose output can be verified.

## What Changes

- Add an MCP server that runs locally over stdio and offers two tools:
  - `search_law`: ranked passages of the corpus for a question, each with its citation label, title, source URL, the "Stand" of the law and the passage text.
  - `ask_law`: a cited answer, or an explicit refusal, as decided by normkompass (the quote checking happens there, not here).
- The server is a thin client of the normkompass HTTP API. It adds no retrieval, no model and no storage of its own.
- Configure it through one environment variable for the API address; no secrets are needed or stored.
- Report problems to the agent as clear tool errors (invalid input, API unreachable, answer model not configured) instead of crashing or returning invented text.
- Test it without a real normkompass instance, using a stub of the API; document how to connect it to an MCP client.

Out of scope: any retrieval or ranking logic, hosting the server remotely, authentication, a second corpus, caching, and any claim about answer quality (that belongs to normkompass and its results).

## Capabilities

### New Capabilities

- `mcp-tools`: the tools the server offers, their inputs and outputs, and how refusals and errors are shown to the agent.
- `normkompass-client`: how the server reaches the normkompass API, its configuration and failure behavior.
- `project-docs`: what the README states and the tested way to connect the server to a client.

### Modified Capabilities

None.

## Impact

- A new Python package with tests and CI; no change to the normkompass repository except a later link in its README.
- Needs a running normkompass API to be useful; `ask_law` additionally needs an answer model configured there.
