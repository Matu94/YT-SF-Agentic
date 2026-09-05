# Release files

Create a CSV file per release: `release_vX_Y_Z.csv` (e.g. `release_v1_1_1.csv` for version 1.1.1).

**Format:** One column `file_path` with SQL file paths relative to repo root. Files are deployed in folder order (01_schemas before 03_tables, etc.).

```csv
file_path
snowflake/01_schemas/TEST_SCHEMA.sql
snowflake/03_tables/orders.sql
snowflake/05_views/revenue_summary.sql
```

**Workflow:** Create the release file on `dev`, then run the "Create release branch" action in GitHub with the version (e.g. `1-1-1`).
