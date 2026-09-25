---
trigger: always_on
---

# Documentation Standards

## 1. Living Documentation Requirement
Any time structural changes, CI/CD pipeline updates, schema modifications, application code, or deployment script modifications (`deploy.py`, `Makefile`, etc.) are made, the corresponding documentation **MUST** be updated within the same pull request/feature implementation.

## 2. Mandatory Agent Directives for Every Change
All AI agents and developers modifying the codebase must strictly adhere to the following two non-negotiable rules before completing any task:
1. **Changelog Maintenance**: Any addition, fix, modification, or deletion **MUST** be documented immediately in [CHANGELOG.md](file:///Users/matu/git/YT-SF-Agentic/CHANGELOG.md) under the `## [Unreleased]` section adhering to [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) categories (`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`). Never leave changes unrecorded.
2. **Release Manifest Registration**: Any newly created, modified, or targeted asset path (e.g. `.sql`, `.py`, `.yml`, `.csv`, `.md`) **MUST** be registered in the active target release file (e.g., `.release/release_v<target>.csv`). Our release pipeline ([.github/workflows/create-release-branch.yml](file:///Users/matu/git/YT-SF-Agentic/.github/workflows/create-release-branch.yml)) strictly cherry-picks *only* the file paths declared in this ledger when promoting from `dev` to `prod`. Unregistered files will be omitted from production releases.

## 3. Protected Documents
The following files are considered living documentation and must be kept perfectly in sync with the codebase state:
*   `CHANGELOG.md` - Tracks the full release history, unreleased features, bug fixes, and semantic versions.
*   `.release/release_v*.csv` - Explicit release manifest ledger governing artifact promotion to `prod`.
*   `.deployment/README.md` - Tracks the technical logic of `deploy.py` and Python deploy implementations.
*   `.github/workflows/README.md` - Tracks the purpose, triggers, and environments of GitHub Action workflows.
*   `docs/cicd/deploy_process.md` - Tracks the high-level functional and technical architecture of the entire GitOps Git-to-Snowflake pipeline.
*   `docs/database/README.md` - Tracks the Snowflake architectural configurations, schema definitions, compute constraints, and RBAC implementation.
*   `.agents/rules/02-data-model.md` - Tracks the foundational Kimball dimensional modeling logic and logical schema mappings.

Always review and update these after altering the DevOps flow, architecture, or data model!