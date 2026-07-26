---
trigger: always_on
---

# Product Requirements Document: YouTube Metrics Pipeline

## 1. Project Overview
A hobby project focused on building an automated data pipeline to extract YouTube channel metrics natively via Snowflake Python Stored Procedures (Snowpark), process them in Snowflake using dbt, and visualize the data in a Streamlit application. The ultimate goal is to provide deep insights into channel and video performance.

## 2. Infrastructure & Environments
*   **Environment:** The project utilizes two environments: **DEV** (for development and feature testing) and **PROD** (for production workloads).
    *   **Data Warehouse (Snowflake):** Dedicated databases for each environment (e.g., `YT_SF_DEV`, `YT_SF_PROD`) will use a 4-layer architecture: `LANDING` (transient raw drops), `RAW` (persistent history), `STAGING` (dbt transformations), and `MART` (analytics presentation).
    *   **Compute Isolation:** Dedicated virtual warehouses are used for CI/CD (`YT_SF_CICD_WH`), data loading (`YT_SF_LOAD_WH`), dbt transformations (`YT_SF_TRANSFORM_WH`), and administration (`YT_SF_ADMIN_WH`), all controlled by dedicated resource monitors to ensure strict cost management (5 Credits/~5 EUR/month for CI/CD & Admin, and 15 Credits/~15 EUR/month for Load & Transform to support project growth).

## 3. Scope & Delivery
*   **Target:** A continuously growing list of various Hungarian YouTube channels.
*   **Delivery Strategy:** Features and new channels are delivered continuously to PROD as soon as they are validated in DEV. We don't rely on phased releases.
*   **Organizational Hierarchy:** Channels are grouped into broader logical units like Studios or Content Networks for aggregate reporting.

## 4. Technical Requirements

### 4.1 Master Data Management
*   **Static Channel Metadata Table:** A dedicated static table (dimension table) must be created to store organizational metadata for all onboarded channels. Attributes should include, but are not limited to:
    *   Organization (e.g., Content Network)
    *   Team/Studio/Creator (e.g., Creator Studio)
    *   Channel Name / ID
    *   Content Type / Niche

### 4.2 Data Ingestion & Refresh Strategy
*   **Extraction Method (Snowpark):** The pipeline will extract data natively using Snowflake Python Stored Procedures, leveraging Snowflake External Network Access to call the YouTube API directly from the warehouse.
*   **Orchestration:** Scheduled via native Snowflake Tasks running 1-2 times per day.
*   **Historical Load:** Full extraction and onboarding of all historical data for newly added channels initially.

### 4.3 Metrics to Collect
*   **Video-Level Data:**
    *   Video length/duration
    *   Number of views
    *   Number of likes
    *   Number of comments
*   **Channel-Level Data:**
    *   Number of subscribers

## 5. Visualization Layer
*   A **Streamlit application** will be built as the presentation layer to generate and explore insights from the collected metrics transformed via dbt.
