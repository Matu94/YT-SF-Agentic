# YouTube Metrics Pipeline

![Status](https://img.shields.io/badge/Status-In%20Development-yellow) ![Snowflake](https://img.shields.io/badge/Built%20on-Snowflake-blue) ![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-red) ![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)

## Project Overview
This project is an automated, end-to-end data pipeline designed to extract YouTube channel and video metrics, process them in Snowflake using dbt, and visualize the insights through an interactive Streamlit application. The ultimate goal is to provide deep insights into channel and video performance.

The entire architecture and codebase are being designed and implemented using an agent-driven development methodology via Google Antigravity.

## Architecture

The pipeline uses a modern, robust data stack built on the following layers:

1. **Extraction (Python)**: A Python-based automation script extracts historical and daily incremental metrics from the YouTube Data API.
2. **Data Warehouse (Snowflake)**: A 4-layer architecture (`LANDING`, `RAW`, `STAGING`, `MART`) ensuring clean separation of transient api data, persistent history, and presentation-ready facts and dimensions.
3. **Transformation (dbt)**: Utilizes the Kimball Dimensional Modeling approach (Star Schema). Handles daily delta calculations, static organization hierarchies mapping (e.g. Cérnagyár -> Fókusz Stúdió), and SCD Type 2 dimension tracking. 
4. **Visualization (Streamlit)**: Serves as the presentation layer to generate and explore insights using the final `MART` schemas.

## Infrastructure & Security

- **Workload Isolation & Cost Control**: Compute is split across dedicated virtual warehouses for CI/CD, extraction loading, transformation, and database administration. Each warehouse's spending is capped via independent Snowflake Resource Monitors.
- **Role-Based Access Control**: Implements a strict two-tier Snowflake RBAC model separating schema-level Object Roles (`_SR`, `_SW`, `_SFULL`) from Functional Roles mapped to the principle of least privilege. 
- **Authentication**: Key-Pair (RSA) authentication is utilized for machine and service users.

For full database documentation, see [docs/database/README.md](docs/database/README.md).

## Project Setup & Status

### Phase 1: The Base (Fókusz Stúdió) - *Current*
- Laying the foundation mapping out the base internal hierarchy for initial tracking.
- Initiating automated Snowflake infrastructure via setup scripts in `.setup/snowflake/`.
- Developing the extraction pipeline and dbt transformations for cumulative metrics and daily delta calculation.

### Phase 2: Future Expansion - *Planned*
- Streamlit Dashboard implementation.
- Extending channel metrics modeling outside of initial seed hierarchy.
