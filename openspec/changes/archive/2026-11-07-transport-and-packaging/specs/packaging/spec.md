## ADDED Requirements

### Requirement: Container image
The repository SHALL contain a container definition that runs the server as a non-root user, takes the API address and any token at run time, and contains no secret in its layers or configuration, and CI SHALL build it.

#### Scenario: Image built in CI
- **WHEN** CI runs on a pull request
- **THEN** the image is built and a failed build fails the check

### Requirement: Image run recorded
The README SHALL state how to run the image for stdio and for HTTP, and SHALL record at least one run against a live normkompass with its date.

#### Scenario: Reader runs the image
- **WHEN** a reader follows the documented command
- **THEN** a client can list the two tools
