# Snowflake DDL & Infrastructure

This directory contains the SQL definitions for the YouTube Metrics Pipeline. All files here are managed and deployed via the `.deployment/deploy.py` engine.

## Universal Object Prefix Map
To ensure consistent execution order and satisfy object dependencies (e.g., creating a Secret before a Procedure), all schemas within `snowflake/` follow this global numbering standard:

| Prefix | Object Type | Description |
| :--- | :--- | :--- |
| **`01_infrastructure`** | Base Objects | File Formats, Network Rules, Secrets, Stages |
| **`02_integrations`** | Connectivity | External Access Integrations |
| **`03_tables`** | Storage | Permanent and Transient Tables |
| **`04_streams`** | CDC | Change Data Capture objects |
| **`05_views`** | Virtualization | Standard and Secure Views |
| **`06_procedures`** | Logic | Snowpark Python Stored Procedures |
| **`07_tasks`** | Automation | Scheduled Tasks and Alerts |

---

## Directory Structure
The pipeline is organized into Medallion layers, with each schema applying the relevant prefixes from the map above:

- **`01_landing/`**:
    - `01_infrastructure/` (e.g., JSON File Format)
    - `03_tables/` (Transient API Landing tables)
- **`02_raw/`**:
    - `03_tables/` (Persistent history)
    - `04_streams/` (Tracking changes for dbt)
- **`03_tech/`**:
    - `01_infrastructure/` (Network Rules, API Secrets)
    - `02_integrations/` (External Access Integrations)
    - `06_procedures/` (Extraction logic)
    - `07_tasks/` (Scheduling)

## Deployment Order
Files are executed in lexicographical order based on:
1. Schema Prefix (`01_landing` -> `02_raw`)
2. Object Prefix (`01_infrastructure` -> `07_tasks`)
3. Filename (e.g., `01_channels.sql` -> `02_videos.sql`)

