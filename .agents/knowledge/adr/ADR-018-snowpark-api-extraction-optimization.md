# ADR 018: Snowpark YouTube API Extraction Optimization (Bulk DML & Concurrent I/O)

## Status
Accepted

## Context
As our tracked Hungarian YouTube channel portfolio grew to 44+ channels with thousands of historical videos, the daily execution of `LANDING.EXTRACT_YOUTUBE_METRICS_SP` on the `YT_SF_LOAD_WH` warehouse began consuming an unsustainable amount of Snowflake credits, threatening the 15-credit monthly cap enforced by `YT_SF_LOAD_RM`.

We evaluated whether to migrate the YouTube API extraction layer out of Snowflake (e.g., to GitHub Actions or AWS Lambda writing to S3) or optimize the existing Snowpark Python Stored Procedure natively.

### Root Cause Analysis of Credit Consumption
An architectural audit of `snowflake/01_landing/06_procedures/EXTRACT_YOUTUBE_METRICS_SP.sql` revealed that the high credit burn is **not** an inherent limitation of Snowpark, but the result of three compounding OLTP and I/O anti-patterns executing on an analytical columnar warehouse:
1. **Row-by-Row DML Inside Loops (Primary Bottleneck):** The procedure executed an individual `INSERT INTO LANDING.YOUTUBE_RAW_DATA (RAW_JSON) SELECT PARSE_JSON(...)` statement for every single channel (44 times) and for every 50-video batch (hundreds of times per run). Because Snowflake is an OLAP columnar database, each standalone `INSERT` incurs query compilation, transaction locking, metadata synchronization, and micro-partition creation overhead (~1–2 seconds per statement).
2. **Unbatched Channel Metadata Requests:** The `/youtube/v3/channels` endpoint was queried sequentially 1-by-1 in a loop (`44` HTTP requests) despite the YouTube Data API v3 supporting up to `50` comma-separated channel IDs per call.
3. **Single-Threaded Synchronous HTTP I/O:** All `playlistItems` pagination loops and `videos` batch requests executed synchronously on a single thread without TCP connection pooling (`requests.get()`), forcing the `YT_SF_LOAD_WH` virtual warehouse to sit idle and billed by the second while waiting on external network round-trips.

### Why Moving Extraction Out of Snowflake Was Rejected
1. **PRD & Architecture Violation:** Our Product Requirements Document (`.agents/rules/00-product-vision.md` § 4.2) and Data Architecture (`.agents/rules/01-data-architecture.md` § 1) explicitly mandate native extraction via Snowpark Python Stored Procedures using Snowflake External Network Access and native Snowflake Tasks.
2. **Regression Against ADR-016:** In **ADR-016**, we intentionally eliminated external GitHub Actions cron runners to unify scheduling, security, and orchestration natively inside Snowflake. Offloading extraction to GitHub Actions or AWS Lambda would re-introduce split orchestration and force us to duplicate `TECH.YOUTUBE_API_KEY_SECRET` outside Snowflake's governance boundary.
3. **The Agentic Pivot Principle:** Per our Agentic Conceptual Framework (`conceptual_framework.md` § 7), we never abandon an architectural boundary until algorithmic optimizations have been exhausted.

## Decision
We will **retain the native Snowpark extraction architecture** inside Snowflake and refactor `LANDING.EXTRACT_YOUTUBE_METRICS_SP` to eliminate row-by-row DML and synchronous network wait times:

1. **In-Memory Payload Accumulation & Single Bulk Write:**
   * All raw JSON API responses (both channel and video payloads) will be accumulated in a Python list in memory during the extraction run.
   * Instead of executing `INSERT` inside the HTTP loops, the procedure will write all payloads into `LANDING.YOUTUBE_RAW_DATA` in a **single bulk operation** at the conclusion of the script (using a Snowpark DataFrame bulk append or batched multi-row `INSERT INTO ... SELECT PARSE_JSON(column1) FROM VALUES ...`).
2. **Batched Channel API Lookups:**
   * Channel IDs will be chunked into batches of up to 50 IDs per request (`id=id1,id2,...`), reducing 44 sequential channel API calls to a single HTTP request.
3. **Concurrent HTTP Fetching & Connection Reuse:**
   * We will use Python's native `concurrent.futures.ThreadPoolExecutor` alongside `requests.Session()` connection pooling to parallelize channel playlist pagination and 50-video batch requests across worker threads.

## Consequences
* **Positive (90–95% Credit Reduction):** Eliminating hundreds of sequential `INSERT` transactions and parallelizing HTTP calls drops total procedure runtime from many minutes to under 30 seconds, billing near the 60-second minimum quantum (~0.016 credits/run, or **~0.5 credits/month**).
* **Positive (Zero Infrastructure Sprawl):** Preserves 100% alignment with `.agents/rules/00-product-vision.md`, `.agents/rules/01-data-architecture.md`, and **ADR-016** without introducing external AWS Lambda functions, IAM roles, or GitHub Actions cron dependencies.
* **Positive (Downstream Transparency):** `LANDING.YOUTUBE_RAW_DATA`, `LANDING.YOUTUBE_RAW_DATA_STREAM`, `RAW.LOAD_YOUTUBE_RAW_DATA_TASK`, and all downstream dbt models remain completely unchanged because the exact same `RAW_JSON` variant payloads are landed.
* **Negative (All-or-Nothing Memory Buffer):** Accumulating JSON payloads in memory before flushing means that if an unhandled fatal exception occurs mid-run, zero rows are written to `LANDING`. However, since `LANDING.YOUTUBE_RAW_DATA` is truncated at the start of every run anyway, atomic batch completion is actually safer than partial landing loads.

## Implementation Notes (For Data Engineer)
* Refactor `snowflake/01_landing/06_procedures/EXTRACT_YOUTUBE_METRICS_SP.sql` using `requests.Session()` and `concurrent.futures.ThreadPoolExecutor(max_workers=8)`.
* Ensure `PARSE_JSON` conversion is handled cleanly via Snowpark DataFrame (`session.create_dataframe` with `parse_json`) or batched `VALUES` clauses without hitting SQL statement size limits.
* Update `docs/database/landing.md` if any procedural flow descriptions change, and register all modified files in `CHANGELOG.md` and the active `.release/release_v*.csv` manifest.
