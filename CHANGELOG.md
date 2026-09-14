# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
