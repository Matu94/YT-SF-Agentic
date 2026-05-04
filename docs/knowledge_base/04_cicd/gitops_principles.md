# CI/CD & GitOps: The Automation Engine

Our CI/CD (Continuous Integration / Continuous Deployment) pipeline is designed to treat Snowflake as a "Target" for our Git repository.

## 1. GitOps Principles
"Git is the Source of Truth." We never change a table definition directly in the Snowflake UI. 
1.  **Modify SQL** in VS Code.
2.  **Commit** to Git.
3.  **The Pipeline** automatically deploys it.
*   **Benefit**: You have a full history (Git Log) of every change ever made to your database.

## 2. The `deploy.py` Engine (SHA256 Idempotency)
Unlike traditional scripts that just "run everything," our custom engine is "smart":
*   **Hashing**: It calculates a SHA256 "fingerprint" for every SQL file.
*   **The History Table**: It checks `TECH.DEPLOYMENT_FILE_HISTORY`. If the hash is already there, it skips the file.
*   **Benefit**: You can run `make deploy` 100 times, and it will only execute the *new* or *modified* files. This is called **Idempotency**.

## 3. Environmental Isolation (DEV vs. PROD)
We use one repository but two distinct worlds:
*   **DEV**: Where you break things, test new Snowpark code, and run dbt experiments.
*   **PROD**: The "Sacred" environment where the Streamlit app gets its data.
*   **Variable Substitution**: Our engine replaces `{{SNOWFLAKE_ENVIRONMENT}}` with either `DEV` or `PROD` at runtime, ensuring the same SQL file works in both places without manual edits.

---
*Created by **Senior DevOps Engineer** — Automation Expert*
