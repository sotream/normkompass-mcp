## ADDED Requirements

### Requirement: Honest README
The README SHALL state what the server is, its status, that it needs a running normkompass API, that `ask_law` needs an answer model configured there, and that answer quality is that of normkompass and not measured here; it SHALL NOT claim production readiness, scalability, legal correctness, customers, or any quality figure.

#### Scenario: Reader checks claims
- **WHEN** a reader compares the README with the repository
- **THEN** every statement matches the code, the tests or a dated recorded run

### Requirement: Tested connection instructions
The README SHALL show how to connect the server to an MCP client, and the instructions SHALL have been run end to end against a live normkompass at least once, with the date and the answer model recorded.

#### Scenario: Reader follows the steps
- **WHEN** a reader follows the connection steps
- **THEN** the client lists the two tools

### Requirement: Checks in CI
CI SHALL run the formatter check, the linter, the type checker, the tests without network access to a real normkompass, and `openspec validate --strict`.

#### Scenario: Pull request
- **WHEN** a pull request is opened
- **THEN** all of these checks run and any failure blocks a green result
