# Presentation Layer: Streamlit Hosting Architecture

## 1. Overview
Our data presentation layer is built on **Streamlit**, a fast and intuitive Python framework for creating data apps. 

To prevent expensive Snowflake Virtual Warehouse compute costs, we export our data to static Parquet files on AWS S3. The Streamlit app reads these files into memory via DuckDB and PyArrow.

## 2. Hosting Evolution (ADR-010 & ADR-014)

### Phase 1: Streamlit-in-Snowflake (SiS)
* **Status:** Deprecated for production (used only for `DEV` testing).
* **Issue:** SiS consumes Snowflake Virtual Warehouse credits for every user interaction, making it financially unviable for public dashboards.

### Phase 2: Streamlit Community Cloud
* **Status:** Deprecated (See [ADR-014](../../../.agents/knowledge/adr/ADR-014-migrate-streamlit-to-aws-apprunner.md)).
* **Issue:** The free Community Cloud tier enforces a strict 1 GB RAM limit. As our historical datasets grew, DuckDB aggregations and Pandas PyArrow conversions frequently exceeded this limit, causing fatal `Out of Memory` errors.

### Phase 3: AWS App Runner (Current Production Standard)
* **Status:** Active.
* **Architecture:** Containerized Streamlit deployment.
* **Why App Runner?** It provides a managed container service with an automated HTTPS URL, zero load balancer configuration, and configurable RAM (e.g., 2 GB or 3 GB) to comfortably handle our DuckDB aggregations, all for a predictable low cost (~$10-12/month).

## 3. Deploying to AWS App Runner

### Prerequisites
1. Ensure the `Dockerfile` is present in the `streamlit/` directory.
2. Push your latest code to the `prod` or `dev` branch on GitHub.

### Setup Process (AWS Console)
1. **Navigate to AWS App Runner** in your AWS Console.
2. Click **Create an App Runner service**.
3. **Source:** Select **Source code repository** (GitHub). 
    * Connect your GitHub account and select the `Matu94/YT-SF-Agentic` repository.
    * Branch: `dev` or `prod`.
    * Trigger: Automatic (rebuilds on push).
4. **Build settings:**
    * Configuration file: Choose **Configure all settings here**.
    * Build command: *(Leave blank, Dockerfile handles this)*
    * Start command: *(Leave blank, Dockerfile handles this)*
    * Port: `8501`.
5. **Service settings:**
    * **Virtual CPU & Memory:** Select `1 vCPU / 2 GB` (or 3 GB if further scaling is needed).
    * **Environment Variables:** You MUST inject your S3 access credentials here so Streamlit can read the Parquet files:
        * `AWS_ACCESS_KEY_ID`
        * `AWS_SECRET_ACCESS_KEY`
        * `S3_BUCKET_NAME` (e.g., `yt-sf-metrics-data-prod`)
        * `AWS_DEFAULT_REGION`
6. **Deploy:** Click Create and Deploy. AWS will build the Docker container and provision a secure `https://...awsapprunner.com` link.

## 4. The Dual-Mode Abstraction
The application continues to support our custom `data_loader.py` abstraction:
1. **Snowflake Native Mode:** If run inside Snowflake, it executes SQL.
2. **S3 Export Mode:** If run on AWS App Runner, it reads the `.parquet` files from the AWS S3 bucket.
