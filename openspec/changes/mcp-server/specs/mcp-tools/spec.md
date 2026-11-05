## ADDED Requirements

### Requirement: Server and transport
The server SHALL run as a local MCP server over stdio and SHALL list exactly two tools, `search_law` and `ask_law`, each with a description that states the corpus (German federal law), that results are not legal advice, and that every result carries the "Stand" of the law it comes from.

#### Scenario: Client lists tools
- **WHEN** an MCP client connects and lists the tools
- **THEN** it receives `search_law` and `ask_law` with descriptions and input schemas

#### Scenario: API is down at startup
- **WHEN** the server starts while the normkompass API is unreachable
- **THEN** it starts and lists its tools without error

### Requirement: Search tool
`search_law` SHALL accept a question (a non-empty text of at most 1000 characters) and an optional limit (an integer from 1 to 20, default 5), and SHALL return the ranked passages with, for each, the source law, the citation label, the title, the source URL, the Stand and the passage text, without changing the order the API returned.

#### Scenario: Matching passages
- **WHEN** the agent calls `search_law` with a question the corpus covers
- **THEN** it receives up to the requested number of passages in the API's order, each with its citation label and URL

#### Scenario: Invalid input
- **WHEN** the question is empty or longer than 1000 characters, or the limit is outside 1 to 20
- **THEN** the tool returns an error that names the invalid field and no request is sent to the API

### Requirement: Ask tool
`ask_law` SHALL accept a question under the same limits and SHALL return what the API decided: for an answer, the answer text and its citations (source, path, URL, quote) and the Stand; for a refusal, a result that says the corpus did not support an answer.

#### Scenario: Cited answer
- **WHEN** the API returns an answer with verified citations
- **THEN** the tool result contains the answer and every citation exactly as returned, and no citation the API did not return

#### Scenario: Refusal
- **WHEN** the API returns a refusal
- **THEN** the tool returns a normal result stating that no supported answer was found, not an error, and contains no answer text

### Requirement: Failures are clear tool errors
The server SHALL report an unreachable API, a timeout, an unexpected response, and an API that has no answer model configured as tool errors with a short plain message that tells the agent what to do or tell the user, and SHALL NOT return invented text, a stack trace or a partial answer.

#### Scenario: Answer model not configured
- **WHEN** the API answers 503 to an ask request
- **THEN** the tool error says that answering is not configured on the normkompass side and that `search_law` still works

#### Scenario: API unreachable
- **WHEN** the API cannot be reached
- **THEN** the tool error names the configured address and says the API is not reachable
