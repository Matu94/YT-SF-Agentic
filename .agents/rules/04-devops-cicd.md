---
trigger: always_on
---

# DevOps & CI/CD Standards: YouTube Metrics Pipeline

## 1. Core Principles
* **Acknowledge Existing Base:** A foundational CI/CD pipeline already exists in this repository. Any CI/CD agent must locate, read, and analyze the existing pipeline configuration files before suggesting or implementing modifications.
* **Do Not Destroy:** Modify and extend the existing pipeline; do not replace it entirely unless explicitly instructed by the user.

## 2. Security & Secret Management
* **Strict Prohibition:** Absolutely no hardcoded credentials. 
* **Secret Injection:** The pipeline must handle all authentication via injected repository secrets. Expected secrets include, but are not limited to:
    * `YOUTUBE_API_KEY`
    * `SNOWFLAKE_ACCOUNT`
    * `SNOWFLAKE_USER`
    * `SNOWFLAKE_PASSWORD`
    * `SNOWFLAKE_ROLE`
    * `SNOWFLAKE_WAREHOUSE`

## 3. Trigger Strategy
* **Manual Dispatches:** The pipeline must support manual triggers (e.g., `workflow_dispatch` in GitHub Actions) for ad-hoc runs and historical backfilling.

## 4. Branch Strategy
* **Primary Branches:** The default development branch is `dev`. Production changes are routed via `prod`. Legacy branches like `main` and `uat` are strictly deprecated and should not be referenced.
* **Working Branches:** Developers operate on `feature/*` or `data*` branches.

## 5. Deployment Framework Expectations
* **Numerical Prefixing for Execution Order:** The `.deployment/deploy.py` script relies on Python's built-in lexicographical sorting to evaluate the execution sequence. You must always use zero-padded integer prefixes in paths (e.g., `00_pre_hooks`, `01_landing`, `99_post_hooks`) to guarantee absolute execution ordering.
* **Seeding Existing State:** The pipeline supports a `make seed` CLI utility. Use this to explicitly register `.sql` files into the Snowflake tracking history (`TECH.DEPLOYMENT_FILE_HISTORY`) so they are inherently skipped by future `deploy` commands.