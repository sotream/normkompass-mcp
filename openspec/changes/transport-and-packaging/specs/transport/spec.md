## ADDED Requirements

### Requirement: Stdio stays the default
The server SHALL start over stdio unless the HTTP transport is selected by configuration, and existing stdio use SHALL NOT change.

#### Scenario: No configuration
- **WHEN** the server is started without transport configuration
- **THEN** it speaks MCP over stdio

### Requirement: Optional HTTP transport on loopback by default
The server SHALL offer an optional streamable-HTTP transport that, unless configured otherwise, listens only on the loopback address.

#### Scenario: Default HTTP start
- **WHEN** the HTTP transport is selected without an address
- **THEN** it listens on the loopback address only

### Requirement: Token required beyond loopback
When the HTTP transport listens on a non-loopback address, the server SHALL require a bearer token from an environment variable and SHALL refuse to start with a clear message when none is set; on a loopback address the token is optional.

#### Scenario: Open address without a token
- **WHEN** the server is configured to listen on a non-loopback address and no token is set
- **THEN** it exits before listening and says that a token is required

#### Scenario: Request without the right token
- **WHEN** a request arrives without a token or with a wrong one while a token is configured
- **THEN** it is rejected before any tool runs, and the response does not reveal the expected value

### Requirement: The token stays secret
The token SHALL be compared in constant time and SHALL NOT appear in logs, error messages, tool results or the README examples as a real value.

#### Scenario: Failed authentication is logged
- **WHEN** a request is rejected for its token
- **THEN** the log entry contains neither the expected token nor the one received

### Requirement: No transport security claimed
The documentation SHALL state that the server does not terminate TLS, that a bearer token over plain HTTP can be read on the network, and that a public deployment is unsupported because the normkompass API behind it has no authentication or limits.

#### Scenario: Reader considers hosting it
- **WHEN** a reader looks for how to expose the server publicly
- **THEN** the README says this is unsupported and why
