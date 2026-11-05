## Context

normkompass exposes `POST /search` (question and a limit from 1 to 20, default 5; a question of at most 1000 characters) returning ranked chunks with source, citation label, title, URL, Stand and text, and `POST /ask` returning an answer with citations, a `refused` flag and the Stand. `/ask` answers 503 when no answer model is configured. The citation check (every quote a verbatim substring of a retrieved chunk) is done in normkompass.

## Decisions

- **Thin client.** Retrieval, ranking and citation checking stay in normkompass. The server only translates between MCP and the HTTP API, so it cannot weaken the verification rule.
- **stdio transport.** It is the transport MCP clients start by default for local servers and needs no network port, no authentication and no hosting.
- **Official MCP Python SDK and an async HTTP client.** The exact libraries and versions are chosen at implementation after checking the current SDK documentation, because that API changes quickly.
- **Refusal is a result, not an error.** When normkompass refuses, the agent gets a normal result saying the corpus did not support an answer, so it can tell the user instead of retrying blindly. Only real failures (invalid input, unreachable API, answer model not configured) are tool errors.
- **No network at startup.** The server starts and lists its tools even when the API is down; the failure shows when a tool is called.
- **Input checks before the network.** The limits of the API (question length, limit range) are checked in the server first so the agent gets the same clear message without a round trip.
- **One setting.** `NORMKOMPASS_API_URL`, default the local address the normkompass quick start uses. Nothing secret is read, logged or sent.
- **Tests against a stub API.** A small in-process stub plays the API, so CI needs neither the corpus, nor Postgres, nor a model. A real end-to-end run against a live normkompass is a manual step, recorded with its date in the README.

## Risks

- The MCP SDK may change; the version is pinned and the choice recorded.
- Passages are quoted law text passed to a model on the client side; the server returns it as data and does not interpret it. Prompt injection through corpus text is a client-side concern that normkompass's own prompt also addresses.
- The server cannot make answers correct; it relays what normkompass decides, and says so in its tool descriptions ("not legal advice", the Stand of each law).
