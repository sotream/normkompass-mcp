# normkompass-client Specification

## Purpose
Reach the normkompass API at one configured address with bounded waiting and checked responses, and no secrets.

## Requirements

### Requirement: Single configured API address
The server SHALL reach normkompass only at the address given by one environment variable, `NORMKOMPASS_API_URL`, with the local default address used in the normkompass quick start, and SHALL send no request to any other host.

#### Scenario: Custom address
- **WHEN** the variable is set to another address
- **THEN** all requests go to that address

#### Scenario: No secrets
- **WHEN** the server runs
- **THEN** it reads, stores and logs no credentials

### Requirement: Bounded waiting
Each request to the API SHALL have a timeout, and a request that exceeds it SHALL end as a tool error and SHALL NOT be retried silently.

#### Scenario: Slow API
- **WHEN** the API does not answer within the timeout
- **THEN** the tool returns a timeout error

### Requirement: Responses are checked
The server SHALL check that an API response has the expected shape before using it and SHALL treat a response without it as an error, never as an empty result.

#### Scenario: Malformed response
- **WHEN** the API returns something that is not the expected shape
- **THEN** the tool returns an error and not an empty list or an empty answer
