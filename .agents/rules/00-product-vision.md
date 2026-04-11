# Product Requirements Document: YouTube Metrics Pipeline

## Executive Summary
This project is an automated data pipeline that extracts YouTube metrics for Hungarian channels via Python, processes the data in Snowflake using dbt, and visualizes the results in a Streamlit application. Built using agentic development, it aims to provide a scalable foundation for hierarchical channel analytics while maintaining cost-effective batch processing.

## Core Objectives
*   **Scalable Foundation:** Establish a strong architectural base capable of scaling up to 20-30 channels in the future, seamlessly introducing new KPIs over time.
*   **Metadata Hierarchy:** Support complex organizational structures by accurately storing and separating data across an Organization > Team > Channel hierarchy.
*   **Cost Efficiency:** Run the automated processing pipeline strictly once a day to minimize operational and compute costs while ensuring daily reporting.
*   **Environment Management:** Implement strictly separated environments for development/testing and production workloads.
*   **Historical Data Onboarding:** Design the system with a clear, robust mechanism for onboarding and backfilling historical video and channel data.

## In-Scope Features (Version 1.0)
*   **Data Extraction & Processing:** A Python script to extract limited key metrics (specifically number of views on videos and subscriber counts) for a small, initial subset of Hungarian YouTube channels, pushed to Snowflake and mapped via dbt.
*   **Visualization (Streamlit):** A clean, premium dark-themed dashboard.
*   **Core Dashboard Metrics:** Visualizations specifically highlighting *daily subscriber growth* and *average views per video*.
*   **Basic Scheduling:** A daily execution trigger for the pipeline.

## Out of Scope (Version 1.0)
*   **Extended Metrics:** Extraction of comments, detailed video-level engagement, and full total/daily subscription change logs (beyond the core dashboard requirements).
*   **Broad Scale Rollout:** Inclusion of the full 20-30 channel roster; V1.0 remains scoped strictly to the initial test channels.
*   **Intraday Refresh:** Running the pipeline more than once a day (e.g., twice daily or real-time streaming).
