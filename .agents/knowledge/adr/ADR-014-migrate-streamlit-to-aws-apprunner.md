# ADR 014: Migrate Streamlit Presentation Layer to AWS App Runner

## Status
Accepted

## Context
Our Streamlit dashboard was historically hosted on Streamlit Community Cloud (ADR-010). However, as our Parquet datasets (specifically `RPT_VIDEO_PERFORMANCE_DAILY`) grew in size, the 1GB RAM limit enforced by Streamlit Community Cloud became a fatal bottleneck, resulting in persistent Out Of Memory (OOM) crashes.

Despite optimizing our Python backend with PyArrow types, DuckDB pushdown predicates, and aggressive Garbage Collection (`@st.cache_data(max_entries=2)` and `gc.collect()`), multi-tenant caching and DuckDB's HTTP range buffers occasionally exceeded the 1GB ceiling during heavy user interaction (filtering multiple channels).

We require a hosting solution that provides:
1. >1 GB of RAM to handle DuckDB aggregations comfortably.
2. A publicly accessible URL.
3. Very low or highly manageable costs.

## Decision
We will migrate the Streamlit presentation layer from Streamlit Community Cloud to **AWS App Runner**.

### Why AWS App Runner?
1. **Managed Service:** It builds and deploys directly from a `Dockerfile` (or GitHub repo) without managing EC2 instances or load balancers.
2. **Built-in HTTPS:** Automatically provisions an AWS-managed domain (`https://xyz.awsapprunner.com`) with an SSL certificate.
3. **Configurable Memory:** We can provision 2 GB, 3 GB, or 4 GB of RAM, giving the Python runtime sufficient headroom.
4. **Cost Structure:** While not $0/month like Community Cloud, it is one of the most cost-effective AWS solutions for containerized web apps (~$10/month for a 2GB instance), completely avoiding the exorbitant costs of AWS Application Load Balancers ($16+/mo) required by AWS ECS Fargate.

## Consequences
* **Positive:** The OOM errors will cease. The application will have sufficient headroom to aggregate larger datasets.
* **Positive:** We retain the "S3 Export Mode" architecture, bypassing Snowflake Virtual Warehouse compute costs.
* **Negative (Financial):** We incur a baseline monthly AWS bill for the App Runner provisioned memory (approx. $10.20/mo for a 2GB container).
* **Negative (DevOps):** We introduce a `Dockerfile` into the repository which must be maintained.

## Implementation Notes
* A `Dockerfile` has been added to the `streamlit/` directory.
* AWS Credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) and `S3_BUCKET_NAME` must be injected as environment variables into the AWS App Runner service configuration rather than Streamlit Secrets (`st.secrets`).
