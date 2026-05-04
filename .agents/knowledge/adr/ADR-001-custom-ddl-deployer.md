# ADR-001: Custom DDL Deployment Engine (`deploy.py`)

## Status
Accepted

## Context
We need a way to deploy Snowflake DDL (infrastructure, base tables, procedures) identically across `DEV` and `PROD` environments. 
Existing tools like `schemachange` or `dbt` (for DDL) were considered, but the project requires:
1.  **Strict Execution Order**: Guaranteed by numerical prefixing (e.g., `01_`, `02_`).
2.  **Native Variable Substitution**: Lightweight replacement of database/warehouse names without complex configuration.
3.  **State Tracking in Snowflake**: Visibility into exactly which file was deployed, by whom, and when, stored directly in a `TECH.DEPLOYMENT_HISTORY` table.
4.  **Agent-Friendly**: A script that an AI agent can easily read, modify, and troubleshoot without deep diving into a proprietary tool's CLI.

## Decision
We implemented a custom Python script `.deployment/deploy.py` that uses:
- `git diff` for change detection.
- SHA256 content hashing to prevent redundant executions.
- `snowflake-connector-python` for direct execution.
- Jinja-like variable substitution (`{{VAR}}`).

## Consequences
- **Positive**: Full control over the deployment lifecycle, easy debugging for AI agents, and zero dependency on heavy external CLI tools.
- **Negative**: We are responsible for maintaining the script logic (no unit tests currently) and it lacks some advanced features of established tools (like automatic rollbacks).
- **Compliance**: All new DDL must be placed in the `snowflake/` directory with a 2-digit numerical prefix.
