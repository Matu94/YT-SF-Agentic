# Frontend & Business Intelligence Standards: YouTube Metrics Pipeline

## 1. Visual & Layout Guidelines (Streamlit UI)
*   **Clean & Simple Aesthetics**: Prioritize a clear, minimalist, and simple user interface design. Avoid layout clutter, utilize clean margins, and present data clearly.
*   **Dark Mode Optimization**: Design exclusively with dark-mode compatibility in mind, leveraging deep background tones, readable contrast, and native dark chart themes.
*   **Grid Layouts**: Use `st.columns()` to display KPI metric cards side-by-side. Do not stack isolated stats vertically.
*   **Typography & Colors**: Maintain visual alignment with the Cérnagyár styling. Use semantic colors for trends (green for growth, red for decline).
*   **Sidebar Navigation**: Keep control widgets (e.g. channel filter, date range, metric picker) in the left sidebar to maximize dashboard space.
*   **Interactive Charting**: Use Altair or Plotly for dynamic charts that support hover tooltips, zoom, and selections.

## 2. Snowflake Native Streamlit Integration
*   **Active Session Context**: Rather than establishing standard network connections, Snowflake Native Streamlit applications must import `get_active_session` to query the database using the active user's environment role:
    ```python
    from snowflake.snowpark.context import get_active_session
    session = get_active_session()
    ```
*   **Environment Configuration (`environment.yml`)**: Define all library dependencies (e.g. `altair`, `pandas`, `snowflake-snowpark-python`) explicitly in `streamlit/environment.yml` to allow the Snowflake container to provision the application correctly.
*   **No Local Disk Storage**: Snowflake Native Streamlit apps run inside a sandbox. Do not attempt to write temp files or persist state to local disk.

## 3. Data Ingestion & Query Best Practices
*   **Kimball Mart Consumption**: All queries inside Streamlit must query `YT_SF_{ENV}.MART.*` models. Directly querying `RAW` or `LANDING` is strictly prohibited.
*   **Offload Transformation to dbt**: The Streamlit app should never compute daily deltas, perform complex parsing (e.g. ISO 8601 strings), or execute multi-join aggregations. These must be performed downstream in dbt staging or marts.
*   **Strict Caching**: To minimize Snowflake credit consumption and speed up load times, use `@st.cache_data` for all database retrieval functions. Set an expiration (e.g. `ttl=3600`) since metrics are only loaded 1-2 times daily.
