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
3. Sets up Python, establishes Key-Pair authentication via ingested GitHub organization secrets (`SNOWFLAKE_PRIVATE_KEY`, `YOUTUBE_API_KEY`), and uses `deploy.py` to calculate file differentials and gracefully roll them out to the Data Warehouse.
4. Spits out a rich Markdown log mapping deployment successes and failures dynamically to the Action's user interface.

### 2. Create Release Branch (`create-release-branch.yml`)
**Purpose**: Serves as the primary automation tool to promote approved changes from the `dev` environment into a static `release/*` tracking branch.

**Triggers**: 
- Strictly manual via `workflow_dispatch` (requires inputting a targeted Version String like `1-1-1`).

**Behavior**:
1. Requires the user to have submitted a `release_v<VER>.csv` file mapping the approved paths inside the `.release` directory on the `dev` branch.
2. Checks out the specific artifacts listed explicitly on the CSV mapping to tightly enforce explicit versioning.
3. Auto-commits the packaged state under a new `release/*` branch natively spanning from `dev` or `prod`. This branch can then be historically reviewed and subsequently merged into the main `prod` trunk.

### 3. Export Streamlit Data to S3 (`export_parquet_s3.yml`)
**Purpose**: Decouples Snowflake compute from Streamlit Community Cloud hosting (per **ADR-010**) by extracting and statically exporting presentation views into AWS S3.

**Triggers**:
- Automatically on a cron schedule (`0 5 * * *` / daily at 05:00 UTC).
- Manual execution via `workflow_dispatch`.

**Behavior**:
1. Maps dynamic environments to identify whether to export from `DEV` or `PROD` databases.
2. Injects securely hosted Snowflake Private Keys and AWS S3 credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`).
3. Executes `.deployment/export_to_s3.py` which dynamically converts 9 Snowflake presentation views (`RPT_*`) into optimized Parquet formats and uploads them to the S3 bucket (`s3://yt-sf-metrics-data-prod/mart/`).

