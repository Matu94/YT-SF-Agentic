# ADR 014: Migrate Streamlit Presentation Layer to DigitalOcean App Platform

## Status
Accepted

## Context
Our Streamlit dashboard was historically hosted on Streamlit Community Cloud (ADR-010). However, the 1GB RAM limit enforced by the free tier became a fatal bottleneck for DuckDB/PyArrow aggregations on our S3 Parquet files, resulting in persistent Out Of Memory (OOM) crashes.

We investigated several hosting alternatives:
1. **AWS App Runner**: Deprecated for new customers as of April 30, 2026.
2. **Amazon ECS Express Mode**: Rejected due to the mandatory Application Load Balancer (ALB) base costs (~$16.50/mo), inflating the total cost to ~$30/mo.
3. **AWS Lightsail Container Service**: Viable ($20/mo for 2GB RAM), but lacks the seamless GitHub CI/CD integration.
4. **DigitalOcean App Platform**: A fully managed PaaS offering 2GB RAM for a flat $12/month, with direct GitHub repository integration.

We require an infrastructure that honors our "almost nothing" cost constraint while providing a robust developer experience (zero-downtime automated deployments from GitHub) and sufficient memory (>1 GB).

## Decision
We will deploy the containerized Streamlit application to **DigitalOcean App Platform**.

### Why DigitalOcean?
1. **Developer Experience (DX):** It provides a Heroku/App Runner-like experience. It reads the repository, builds the `Dockerfile`, handles TLS/HTTPS via Let's Encrypt automatically, and manages the domain.
2. **Cost Predictability:** The Basic tier provisions 2 GB RAM and 1 vCPU for a flat rate of **$12.00 / month**. There are no surprise Load Balancer or egress network fees typical in AWS.
3. **Automation:** Code pushed to the `dev` or `prod` branch will automatically trigger a rebuild and deployment, replicating the Streamlit Community Cloud workflow exactly.

## Consequences
* **Positive:** The OOM errors will be resolved by the 2GB memory ceiling.
* **Positive:** We retain a fully automated GitOps deployment flow.
* **Positive:** Complete avoidance of AWS Load Balancer cost traps.
* **Negative (Financial):** We transition from a $0/month hosting bill to a fixed $12/month bill.

## Implementation Notes
* A `Dockerfile` has been added to the `streamlit/` directory to facilitate the App Platform build.
* AWS Credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) and the S3 Bucket details must be injected as environment variables in the DigitalOcean App Platform console to allow secure fetching of the Parquet files.
