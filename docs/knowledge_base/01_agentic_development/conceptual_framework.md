# Agentic Development: The Conceptual Framework

In this project, we aren't just "writing code with AI"—we are practicing **Agentic Development**. This document explains the core concepts that make this repository "AI-ready."

## 1. Why do we need Personas?
An LLM is a generalist. If you ask it to "fix the code," it might suggest a quick hack that breaks your architecture. By using **Personas** (like `Data Architect`, `Data Engineer`, or `Data Analyst`), we:
*   **Restrict the "Search Space"**: Each persona only looks at specific rules and tools.
*   **Set the Tone**: A `Data Architect` will focus on the "Why" and "Scalability," while a `Data Engineer` will focus on "Idempotency" and "Syntax."
*   **Prevent Hallucination**: Personas help the AI stay in its lane.

## 2. The PRD (Product Requirements Document)
Located in `.agents/rules/00-product-vision.md`.
*   **Purpose**: It defines the "What" and "Who."
*   **Agentic Role**: It is the "Anchor of Truth." If the agent suggests adding a Twitter connector, the PRD will stop it because the scope is restricted to YouTube.
*   **Analogy**: The PRD is the **Goal Post**.

## 3. The ADR (Architecture Decision Record)
Located in `.agents/knowledge/adr/`.
*   **Purpose**: It documents **Why** a specific technical choice was made (e.g., "Why use `deploy.py` instead of `schemachange`?").
*   **Agentic Role**: It prevents the AI from "re-suggesting" alternatives you've already rejected. It gives the agent the "Context of History."
*   **Analogy**: The ADR is the **Map of Past Decisions**.

## 4. The Atomic Task Rule (Mastering the Scope)
A common mistake is asking an agent for a "Mega-Task" (e.g., "Set up the whole database"). This forces the agent to make too many assumptions at once.
*   **The Best Practice**: Break goals into **Atomic Tasks**—steps that have a clear beginning, middle, and end.
*   **Current Project Example**: Instead of "Set up RBAC," we broke it into:
    1.  Initialize Infrastructure (`00_infrastructure_init.sql`).
    2.  Define Object Roles (`01_role_init.sql`).
    3.  Grant Privileges (`02_grant_init.sql`).
*   **Benefit**: If Step 2 fails, the context is small enough to fix easily without re-reading the entire project's history.

## 5. The "Steering Wheel" (Human-in-the-Loop)
In this project, you (the Human) are the **Pilot**, and I am the **Auto-pilot**. 
*   **The Pilot's Duty**: You are the final Quality Control. You should never assume the AI's first draft is perfect.
*   **Effective Feedback**: If an agent makes a mistake, don't just say "it's wrong." Provide the **Error Log** or the **Expected vs. Actual** result.
*   **Steering**: If you see the agent going down a "rabbit hole" (e.g., over-complicating a simple Python script), use your authority to say: *"Stop. Let's simplify this. Use a basic loop instead of a complex generator."*

## 6. "Context is King"
Agents work best when they have a "Mental Model" of the repository. We provide this through:
*   **Living Documentation**: READMEs that are updated every time the code changes.
*   **Directory Prefixes**: The `01_`, `02_` prefixes tell the agent (and the human) the exact execution order without reading the scripts.

---
*Created by **Antigravity** — Architectural Conscience*

## 7. The Agentic Pivot (Adapting to Physical Limits)
Agentic systems must be flexible enough to pivot architecture when code optimizations exhaust physical limits.
*   **The Scenario**: Our presentation layer on Streamlit Community Cloud (1GB RAM limit) hit severe `Out of Memory` crashes.
*   **The Agentic Process**: We did not immediately spend money. We first attempted aggressive algorithmic optimizations (`max_entries=2`, PyArrow, DuckDB pushdown) in Option C. Only when those physical limits were mathematically proven to be insufficient did we formally adopt a new architecture.
*   **The Pivot**: We issued `ADR-014`, migrated to DigitalOcean App Platform (2GB RAM), and instantly propagated that context shift across all documentation (`READMEs`, `streamlit_hosting.md`, `deploy_process.md`) to maintain the single source of truth for future agents.

## 8. The Native Warehouse Consolidation & Environment Isolation Pivot (ADR-016)
Architecture should eliminate redundant hops and enforce strict environment isolation across third-party clouds.
*   **The Scenario**: Our presentation layer decoupling was originally orchestrated via a GitHub Actions cron job executing a Python script that queried Snowflake, parsed data into Pandas DataFrames, serialized them into Parquet, and uploaded them to S3.
*   **The Agentic Process**: We recognized two architectural vulnerabilities:
    1. *Runner Fragility & Network Egress*: Passing analytical datasets through ephemeral GitHub Actions runners was slow, bottlenecked on memory, and introduced unnecessary operational dependencies.
    2. *Environment Bleed*: Both DEV and PROD were initially writing into the same production S3 bucket, risking staging validation corrupting production metrics.
*   **The Consolidation**: We authored `ADR-016`, eliminating the GitHub Action and intermediate Python script in favor of native Snowflake Tasks (`MART.EXPORT_MART_TO_S3_TASK`) and Stored Procedures executing `COPY INTO <location>` directly through Snowflake Storage Integrations.
*   **The Multi-Environment Standard**: We provisioned an isolated `yt-sf-metrics-data-dev` bucket alongside `yt-sf-metrics-data-prod`, extended our deployment engine (`deploy.py`) with lowercase environment interpolation, and updated IAM policies and living documentation within the exact same release cycle.

## 9. The Mandatory Agent Directives: Changelog & Release Ledger Governance
To eliminate "human cleanup debt," every agent persona is bound to `.agents/rules/05-documentation.md`.
*   **The Vulnerability**: Agents previously wrote high-quality code and modified schemas, but failed to record their work in `CHANGELOG.md` or register altered files in `.release/release_v*.csv`. Because our production promotion workflow (`create-release-branch.yml`) strictly cherry-picks *only* files listed in the release CSV, unregistered assets were orphaned on `dev`.
*   **The Architectural Standard**: All agent personas (`Data Architect`, `Data Engineer`, `DevOps Engineer`, `BI Developer`, `Data Analyst`, `Product Manager`, `Antigravity`) are explicitly codified to mandate:
    1.  *Atomic Changelog Maintenance*: Logging all additions, changes, and fixes immediately under `## [Unreleased]` adhering to Keep a Changelog standards.
    2.  *Manifest Ledger Registration*: Appending all modified or created repository asset paths to the active target `.release/release_v<target>.csv`.
    3.  *Strict Persona Verification*: Antigravity acts as the project gatekeeper, blocking promotion or PR completion if these two artifacts are missing.

