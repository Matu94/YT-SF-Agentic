# Product Requirements Document: YouTube Metrics Pipeline

## 1. Project Overview
A hobby project focused on building an automated data pipeline to extract YouTube channel metrics via a Python script, process them in Snowflake using dbt, and visualize the data in a Streamlit application. The ultimate goal is to provide deep insights into channel and video performance.

## 2. Infrastructure & Environments
*   **Environment:** Initially, only **1 environment (PROD)** will be used to build the foundational architecture and onboard the first set of channels.

## 3. Scope & Phasing
### Phase 1: The Base (Fókusz Stúdió)
*   **Target Channels (4):**
    *   [Fókusz Csoport](https://www.youtube.com/@fokuszcsoport)
    *   [Jólvanezígy](https://www.youtube.com/@jolvanezigy)
    *   [Kókusz Plusz](https://www.youtube.com/@KokuszPlusz)
    *   [Világjegy Csatorna](https://www.youtube.com/@vilagjegycsatorna)

*   **Organizational Hierarchy:**
    *   These initial channels are managed by **Fókusz Stúdió**.
    *   Fókusz Stúdió is a member of the broader organization, **Cérnagyár**.

### Phase 2: Future Expansion
*   **Cérnagyár Expansion:** Onboarding many other content creators and channels housed under Cérnagyár.
*   **External Expansion:** Onboarding channels outside of Cérnagyár across various content types (e.g., cars, news, kitchen, etc.).

## 4. Technical Requirements

### 4.1 Master Data Management
*   **Static Channel Metadata Table:** A dedicated static table (dimension table) must be created to store organizational metadata for all onboarded channels. Attributes should include, but are not limited to:
    *   Organization (e.g., Cérnagyár)
    *   Team/Studio (e.g., Fókusz Stúdió)
    *   Channel Name / ID
    *   Content Type / Niche

### 4.2 Data Ingestion & Refresh Strategy
*   **Historical Load:** Full extraction and onboarding of all historical data for newly added channels initially.
*   **Ongoing Updates:** Incremental daily updates running **1-2 times per day** to capture the latest metrics.

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
