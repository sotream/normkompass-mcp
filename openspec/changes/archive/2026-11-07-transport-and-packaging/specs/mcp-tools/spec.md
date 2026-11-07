## ADDED Requirements

### Requirement: Truthful tool annotations
Both tools SHALL carry the MCP tool annotations that describe them as read-only, not destructive, and idempotent, and SHALL NOT claim any annotation that is not true; the documentation SHALL describe annotations as hints for clients and not as a security control.

#### Scenario: Client lists tools
- **WHEN** an MCP client lists the tools
- **THEN** each tool shows the read-only, non-destructive and idempotent annotations
