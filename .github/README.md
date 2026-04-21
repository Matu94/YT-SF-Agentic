# CI/CD Workflows

This directory configures the GitHub Actions workflows responsible for orchestrating automated testing, deployments, and environment promotions.

## Workflows Structure

### 1. Snowflake Deploy (`snowflake-deploy.yml`)
**Purpose**: Automates the rollout of DDL changes to the Snowflake Infrastructure securely and transparently.

**Triggers**: 
- Push events to the `snowflake/**` directory on the `dev`, `prod`, `feature/*`, and `data*` branches.
- Manual execution via `workflow_dispatch` (allowing specific overrides to deployment modes like changing from diff-based to log-based full deploys).

**Behavior**:
1. Checks the triggered branch to determine the Environment (`dev` vs `prod`).
2. Leverages the bespoke pipeline-runner securely inside an AWS subnet.
3. Sets up Python, establishes Key-Pair authentication via ingested GitHub organization secrets (`SNOWFLAKE_PRIVATE_KEY`), and uses `deploy.py` to calculate file differentials and gracefully roll them out to the Data Warehouse.
4. Spits out a rich Markdown log mapping deployment successes and failures dynamically to the Action's user interface.

### 2. Create Release Branch (`create-release-branch.yml`)
**Purpose**: Serves as the primary automation tool to promote approved changes from the `dev` environment into a static `release/*` tracking branch.

**Triggers**: 
- Strictly manual via `workflow_dispatch` (requires inputting a targeted Version String like `1-1-1`).

**Behavior**:
1. Requires the user to have submitted a `release_v<VER>.csv` file mapping the approved paths inside the `.release` directory on the `dev` branch.
2. Checks out the specific artifacts listed explicitly on the CSV mapping to tightly enforce explicit versioning.
3. Auto-commits the packaged state under a new `release/*` branch natively spanning from `dev` or `prod`. This branch can then be historically reviewed and subsequently merged into the main `prod` trunk.
