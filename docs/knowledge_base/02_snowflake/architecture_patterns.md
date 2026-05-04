# Snowflake Architecture: The YouTube Pipeline Pattern

Even for Snowflake experts, the "Agentic" approach to Snowflake has specific patterns that ensure automation and security.

## 1. The Medallion Architecture
We use a 4-layer approach to ensure data quality:
1.  **LANDING (Transient)**: A "temporary parking lot" for raw JSON. We use `TRANSIENT` tables here to save on storage costs because we can always re-run the API if needed.
2.  **RAW (Persistent)**: The "Source of Truth." Once data leaves Landing, it is merged here and never deleted.
3.  **STAGING (Processing)**: Where we calculate the "Deltas." Since YouTube API gives cumulative views (Total Views to date), Staging calculates `Today - Yesterday`.
4.  **MART (Presentation)**: The final Star Schema (Facts and Dimensions) optimized for Streamlit.

## 2. RBAC: Functional vs. Object Roles
We use a "Two-Tier" role model:
*   **Object Roles**: (e.g., `_SR` for Read, `_SW` for Write). These are tied to specific schemas.
*   **Functional Roles**: (e.g., `LOAD_ROLE`, `TRANSFORM_ROLE`). We grant the Object Roles to these Functional Roles.
*   **Why?**: This makes security "Plug and Play." If you hire a new developer, you just give them the `TRANSFORM_ROLE`, and they automatically get the right access to Raw, Staging, and Mart.

## 3. The `TECH` Schema
*   **Purpose**: This is the "Admin Room" of the database. 
*   **Contents**: It holds the `DEPLOYMENT_HISTORY` tables for our Python script and the `SECRETS`/`NETWORK RULES` for the YouTube API.
*   **Rule**: Data Engineers should never store business data in `TECH`.

---
*Created by **Principal Data Architect** — Strategic Visionary*
