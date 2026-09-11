# Presentation Layer: Streamlit Hosting Architecture

## 1. Overview
Our data presentation layer is built on **Streamlit**. To prevent expensive Snowflake Virtual Warehouse compute costs, we export our data to static Parquet files on AWS S3. The Streamlit app reads these files into memory via DuckDB and PyArrow.

## 2. Hosting Evolution (ADR-010 & ADR-014)

### Phase 1: Streamlit-in-Snowflake (SiS)
* **Status:** Deprecated for production (used only for `DEV` testing).

### Phase 2: Streamlit Community Cloud
* **Status:** Deprecated (See [ADR-014](../../../.agents/knowledge/adr/ADR-014-migrate-streamlit-to-digitalocean.md)).
* **Issue:** The free Community Cloud tier enforces a strict 1 GB RAM limit, leading to DuckDB/PyArrow Out Of Memory (OOM) crashes on large tables.

### Phase 3: DigitalOcean App Platform (Current Production Standard)
* **Status:** Active.
* **Architecture:** Containerized Streamlit deployment driven by a `Dockerfile`.
* **Why DigitalOcean over AWS?** AWS App Runner was deprecated, and the AWS ECS replacement carries high Load Balancer fees (~$30/mo total). DigitalOcean App Platform provides an identical managed container experience with direct GitHub integration and 2 GB RAM for a flat **$12 / month**.

## 3. Deploying to DigitalOcean App Platform

### Prerequisites
1. You must have a DigitalOcean account linked to your GitHub.
2. Ensure the `Dockerfile` is present in the `streamlit/` directory.

### Setup Process (DigitalOcean Console)
1. **Create an App:**
    * Log into DigitalOcean and click **Create -> Apps**.
2. **Choose Source:**
    * Select **GitHub**.
    * Choose the `Matu94/YT-SF-Agentic` repository.
    * Select the branch (e.g., `dev` or `prod`).
    * Source Directory: `/streamlit` (Important: Point this to the folder containing the `Dockerfile`).
    * Ensure "Autodeploy" is checked.
3. **Configure the Resource:**
    * DigitalOcean will auto-detect the `Dockerfile`.
    * **HTTP Port:** Set to `8501`.
4. **Environment Variables:**
    * You MUST inject your AWS credentials so the Streamlit app can securely fetch the Parquet files from S3:
        * `AWS_ACCESS_KEY_ID`
        * `AWS_SECRET_ACCESS_KEY`
        * `S3_BUCKET_NAME` (e.g., `yt-sf-metrics-data-prod`)
        * `AWS_DEFAULT_REGION` (e.g., `eu-north-1`)
5. **Select Plan:**
    * Choose the **Basic Plan**.
    * Select the **$12.00/mo** container size (1 vCPU, 2 GB RAM). *Do not select the $5 plan, as 1 GB RAM will cause OOM crashes.*
6. **Launch:** Click "Review App" and then "Create App".

DigitalOcean will build the Docker container and automatically assign a secure HTTPS domain (e.g., `https://yt-sf-dashboard-xyz.ondigitalocean.app`) that can be shared immediately.
