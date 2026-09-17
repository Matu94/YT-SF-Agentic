# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **S3 Development Environment Isolation**: Created dedicated AWS S3 bucket `yt-sf-metrics-data-dev` to maintain complete data isolation between DEV and PROD environments.
- **Deployer Interpolation Features**: Enhanced `deploy.py` to support `{{SNOWFLAKE_ENVIRONMENT_LOWER}}` and `{{S3_BUCKET_NAME}}` placeholder interpolation for dynamic environment-specific stage URLs.

### Changed
- **S3 Parquet Export Pipeline**: Migrated Parquet data export from GitHub Actions Python runner to native Snowflake Task (`MART.EXPORT_MART_TO_S3_TASK`) and Stored Procedure (`MART.EXPORT_MART_TO_S3`) using `COPY INTO` External Stage ([ADR-016](.agents/knowledge/adr/ADR-016-snowflake-native-s3-export.md)).
- **Export Task Schedule**: Configured daily execution trigger to `02:30 Europe/Budapest` running on `YT_SF_TRANSFORM_WH`.

### Removed
- **Legacy Export Infrastructure**: Removed `.deployment/export_to_s3.py` and `.github/workflows/export_parquet_s3.yml`.

---

## [1.0.2] - 2026-09-15

### Added
- **Default Channel Preselections**: Added "ATV Magyarország" and "the Zone" to the default channel selection in Video Statistics.
- **Expanded Channel Multi-Select**: Increased maximum selectable channels from 5 to 10 in the Video Statistics filter.

### Changed
- **Streamlit Video Statistics Layout**: Unified *Trend Analysis* and *Top Performing Videos* into a single continuous page layout, eliminating tabbed navigation.
- **Streamlit Leaderboards UX**: Retained expanded sidebar on page load.
- **Global Chart UX**: Disabled interactive zoom/pan on all Altair charts across the app to prevent scroll-jacking.
- **S3 Parquet Export Schedule**: Adjusted daily Snowflake Task trigger to `02:30 Budapest time`.
- **Streamlit Documentation**: Fixed page numbering in `streamlit/README.md` to align with actual page file names.

---

## [1.0.1] - 2026-09-13

### Added
- **Cloudflare Edge Proxy**: Routed public web traffic through Cloudflare for global DNS management, unmetered DDoS mitigation, and edge asset caching ([ADR-015](.agents/knowledge/adr/ADR-015-cloudflare-edge-layer-and-custom-domain.md)).
- **Custom Production Domain**: Bound the Streamlit presentation layer to [https://ytmetrics.matudata.com](https://ytmetrics.matudata.com).
- **Edge Layer Architecture Docs**: Updated high-level architecture diagram and flowcharts to include Cloudflare proxy and edge caching.

### Changed
- Promoted project status in `README.md` to **Milestone 1 Live**.
- Documented Phase 4 hosting architecture in `docs/knowledge_base/07_presentation_layer/streamlit_hosting.md`.

---

## [1.0.0] - 2026-09-11

### Added
- **Snowpark API Ingestion**: Automated YouTube Data API v3 extraction via native Snowflake Python Stored Procedures and External Network Access.
- **Kimball Dimensional Modeling (dbt)**: Star schema modeling featuring dimensions (`dim_channel`, `dim_video`, `dim_date`) and daily/rolling facts (`fct_daily_*`, `fct_rolling_7d_*`, `fct_rolling_30d_*`).
- **Reporting Layer (OBT Views)**: Pre-aggregated One Big Table views (`rpt_channel_performance_*`, `rpt_video_performance_*`, `rpt_top_video_*`) bounded to `T-1` daily data.
- **Decoupled S3 Parquet Pipeline**: Daily automated extraction pipeline (`export_to_s3.py`, `export_parquet_s3.yml`) with Hive partitioning by channel (`ADR-010`).
- **Interactive Streamlit Application**: Multi-page analytical presentation layer with embedded DuckDB predicate pushdown, Altair visual analytics, and rank leaderboards.
- **DigitalOcean App Platform Hosting**: Migrated to a managed 2 GB RAM container deployment to eliminate OOM bottlenecks ([ADR-014](.agents/knowledge/adr/ADR-014-migrate-streamlit-to-digitalocean.md)).
- **Idempotent DDL Deployment Engine**: Python-driven schema deployment engine (`deploy.py`) utilizing SHA256 checksums and automated table backup/restore safety nets.
