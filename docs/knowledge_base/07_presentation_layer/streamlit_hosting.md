# Presentation Layer: Streamlit Hosting Architecture

## 1. Overview
Our data presentation layer is built on **Streamlit**. To prevent expensive Snowflake Virtual Warehouse compute costs, we export our data to static Parquet files on AWS S3. The Streamlit app reads these files into memory via DuckDB and PyArrow.

## 2. Hosting Evolution (ADR-010 & ADR-014)

### Phase 1: Streamlit-in-Snowflake (SiS)
* **Status:** Deprecated for production (used only for `DEV` testing).

### Phase 2: Streamlit Community Cloud
* **Status:** Deprecated (See [ADR-014](../../../.agents/knowledge/adr/ADR-014-migrate-streamlit-to-digitalocean.md)).
* **Issue:** The free Community Cloud tier enforces a strict 1 GB RAM limit, leading to DuckDB/PyArrow Out Of Memory (OOM) crashes on large tables.

### Phase 3: DigitalOcean App Platform (Compute Standard)
* **Status:** Active.
* **Architecture:** Containerized Streamlit deployment driven by a `Dockerfile`.
* **Why DigitalOcean over AWS?** AWS App Runner was deprecated, and the AWS ECS replacement carries high Load Balancer fees (~$30/mo total). DigitalOcean App Platform provides an identical managed container experience with direct GitHub integration and 2 GB RAM for a flat monthly fee.

### Phase 4: Cloudflare Edge Layer & Custom Domain (ADR-015)
* **Status:** Active (Production Standard).
* **Live Domain:** `https://ytmetrics.matudata.com`
* **Architecture:** DigitalOcean App Platform origin shielded behind Cloudflare's global edge network (DNS + CDN + WAF).
* **Why Cloudflare?**
  1. **Container Resource & Bandwidth Shield:** Protects the single 2GB RAM / 1-vCPU container and the 200 GB monthly bandwidth quota from scrapers, crawlers, and DDoS attacks.
  2. **Free Edge Caching:** Caches static Streamlit frontend assets (JavaScript, CSS, fonts, Altair bundles) at 300+ edge locations worldwide.
  3. **Custom Domain Branding:** Replaces the default `*.ondigitalocean.app` subdomain with a professional custom hostname: `ytmetrics.matudata.com`.
  4. **Native WebSocket Support:** Seamlessly proxies Streamlit's real-time WebSocket connection (`_stcore/stream`).

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
    * Choose the **Basic Plan** (1 vCPU, 2 GB RAM). *Do not select the $5 plan, as 1 GB RAM will cause OOM crashes.*
6. **Launch:** Click "Review App" and then "Create App".

## 4. Cloudflare Edge & Custom Domain Configuration

To connect `ytmetrics.matudata.com` securely without infinite redirect loops:

1. **DigitalOcean App Platform Domain Binding:**
    * Go to **App Platform ➔ sf-yt-metrics ➔ Networking ➔ Domains**.
    * Add domain `ytmetrics.matudata.com` and select **"You manage your domain"**.
2. **Cloudflare DNS Record:**
    * Add a `CNAME` record:
      * **Type:** `CNAME`
      * **Name:** `ytmetrics`
      * **Target:** `sf-yt-metrics-5u96c.ondigitalocean.app` (pure hostname, no `https://` or `/`)
      * **Proxy status:** **Proxied** (Orange Cloud ☁️ enabled).
3. **Cloudflare SSL/TLS Encryption Mode:**
    * In Cloudflare **SSL/TLS ➔ Overview**, set encryption mode to **Full** (or **Full (Strict)**).
    * *Anti-Pitfall:* Never use "Flexible" mode, as DigitalOcean enforces HTTPS and will trigger an infinite `ERR_TOO_MANY_REDIRECTS` loop.
4. **Cloudflare WebSockets:**
    * Under **Network**, verify **WebSockets** is toggled **ON** to support Streamlit runtime event streaming.
