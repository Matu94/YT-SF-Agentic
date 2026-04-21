# Deploy Process Documentation: Technical & Functional

## 1. Functional Overview
Our Data Engineering infrastructure utilizes an automated GitOps methodology. By maintaining Infrastructure-as-Code natively in `.sql` files tied into the repository's continuous integration environment, data warehouse deployments remain explicitly trackable, repeatable, and easily scalable. 

Deployment centers on generating cryptographic hashes of SQL files to assure idempotent, duplicate-free execution upon Snowflakes backplane. 

### The Developer Flow
1. **Branch Checkout**: Developers checkout feature branches (e.g. `feature/YT_metric_changes`) off the primary `dev` branch.
2. **File Generation**: Modifying schema definitions securely inside the structured folder hierarchy (`snowflake/02_RAW/01_tables/user_metrics.sql`).
3. **Local Testing**: Running `make dry-run` to compile environment substitutions locally.
4. **Push & Review**: Pushing up triggers a `dev` synchronization directly to the Development Data Warehouse via `.github/snowflake-deploy.yml`.

## 2. Technical Architecture 

### System Entities
1. **GitHub Pipeline Runner**: (`atmos-aws-arc-runner-set`). Serves as the host executor.
2. **Deploy orchestrator**: `.deployment/deploy.py`. Evaluates Git changes, generates hashes, runs queries, and maintains state tables.
3. **Snowflake Backend**: Stores raw resources, along side two specialized `TECH` tables which record process metadata.

### Infrastructure Trackers: The `TECH` schema
Under our `TECH` schema on Snowflake reside two crucial metadata tables updated sequentially by the deployment pipeline:

*   **`TECH.DEPLOYMENT_HISTORY`**
    Tracks whole-deployment batches. 
    `{DEPLOYMENT_ID, FOLDER_NAME, COMMIT_SHA, DEPLOYMENT_STATUS, START_TIME, BRANCH_NAME}`
*   **`TECH.DEPLOYMENT_FILE_HISTORY`**
    Granularly tracks the actual SQL artifacts ran during a deployment cycle. File hashes are compared against this table prior to attempting execution.
    `{DEPLOYMENT_ID, FILE_PATH, FILE_HASH, STATUS, ERROR_MESSAGE, DEPLOYED_AT}`

### File Ordering Mechanism
The project natively guarantees synchronization ordering due to the numeric format of schemas/folders (e.g. `00`, `01`, `99`). The `deploy.py` execution sequence natively sorts incoming file paths algorithmically (`all_files.sort()`) ensuring Pre-SQL scripts, raw data layers, transformed semantic targets, and post run functions execute functionally decoupled but orderly synchronized. 

## 3. The `seed` Utility Paradigm 
If an environment instance already functionally encapsulates raw definitions, re-executing `CREATE OR REPLACE` commands destroys historical metrics. We leverage a "Seeding" pattern:

1. Executing `make seed` instructs the Python architecture to bypass Snowflake DDL command transmission (`cur.execute(sql)`).
2. The orchestrator isolates all structural SQL definitions and cryptographically calculates them.
3. Those hashes are loaded quietly into the `TECH.DEPLOYMENT_FILE_HISTORY` table tagged entirely as `SUCCESS`.
4. From then on, standard active deployments natively skip over the artifacts because they appear fully executed on the DB backend.

## 4. Release Strategy
Deployments into `PROD` rely on explicitly approved `csv` ledgers defining changes mathematically packaged into isolated Release branches (`.github/create-release-branch.yml`). The target `prod` branch strictly evaluates changes packaged through this promotion utility to preserve a rigid separation from volatile feature pushes.
