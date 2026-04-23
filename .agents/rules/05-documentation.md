---
trigger: always_on
---

# Documentation Standards

## 1. Living Documentation Requirement
Any time structural changes, CI/CD pipeline updates, or deployment script modifications (`deploy.py`, `Makefile`, etc.) are made, the corresponding documentation **MUST** be updated within the same pull request/feature implementation.

## 2. Protected Documents
The following files are considered living documentation and must be kept perfectly in sync with the codebase state:
*   `.deployment/README.md` - Tracks the technical logic of `deploy.py` and Python deploy implementations.
*   `.github/workflows/README.md` - Tracks the purpose, triggers, and environments of GitHub Action workflows.
*   `docs/cicd/deploy_process.md` - Tracks the high-level functional and technical architecture of the entire GitOps Git-to-Snowflake pipeline.
*   `docs/database/README.md` - Tracks the Snowflake architectural configurations, schema definitions, compute constraints, and RBAC implementation.
*   `.agents/rules/02-data-model.md` - Tracks the foundational Kimball dimensional modeling logic and logical schema mappings.

Always review and update these after altering the DevOps flow, architecture, or data model!