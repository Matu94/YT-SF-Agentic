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