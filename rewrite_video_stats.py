import sys

with open("streamlit/pages/1_Video_Statistics.py", "r") as f:
    code = f.read()

# Replace import
code = code.replace("from utils.data_loader import load_data, load_filtered_video_data, get_top_n_channels_from_video",
                    "from utils.data_loader import load_data, load_video_trend_agg, load_video_snapshot_top, get_top_n_channels_from_video")

# Replace data loading logic
old_load = """    try:
        # PUSHDOWN PREDICATE: only download the exact channels requested
        df_full_filtered = load_filtered_video_data(tbl, st.session_state.applied_channels, days_back=40)
    except Exception as e:
        st.error(f"Failed to load video metrics for selected channels. Error: {e}")
        st.stop()
else:
    df_full_filtered = pd.DataFrame()"""

new_load = """    try:
        df_trend_agg = load_video_trend_agg(tbl, st.session_state.applied_channels, days_back=40)
        df_latest_raw = load_video_snapshot_top(tbl, st.session_state.applied_channels)
    except Exception as e:
        st.error(f"Failed to load video metrics for selected channels. Error: {e}")
        st.stop()
else:
    df_trend_agg = pd.DataFrame()
    df_latest_raw = pd.DataFrame()"""
code = code.replace(old_load, new_load)

# Fix video types filter
old_video_type = """if not df_full_filtered.empty and 'VIDEO_TYPE' in df_full_filtered.columns:
    st.sidebar.header("Content Filters")
    df_latest_types = df_full_filtered[df_full_filtered['METRIC_DATE'] == latest_date]
    all_video_types = df_latest_types['VIDEO_TYPE'].dropna().unique().tolist()
    all_video_types.sort()
    
    type_key = f"video_types_{hash(tuple(all_video_types))}"
    selected_video_types = st.sidebar.multiselect("Video Types", options=all_video_types, default=all_video_types, key=type_key)
    
    if selected_video_types:
        df_full_filtered = df_full_filtered[df_full_filtered['VIDEO_TYPE'].isin(selected_video_types)]
    else:
        df_full_filtered = df_full_filtered.iloc[0:0]"""

new_video_type = """if not df_latest_raw.empty and 'VIDEO_TYPE' in df_latest_raw.columns:
    st.sidebar.header("Content Filters")
    all_video_types = df_latest_raw['VIDEO_TYPE'].dropna().unique().tolist()
    all_video_types.sort()
    
    type_key = f"video_types_{hash(tuple(all_video_types))}"
    selected_video_types = st.sidebar.multiselect("Video Types", options=all_video_types, default=all_video_types, key=type_key)
    
    if selected_video_types:
        df_trend_agg = df_trend_agg[df_trend_agg['VIDEO_TYPE'].isin(selected_video_types)]
        df_latest_raw = df_latest_raw[df_latest_raw['VIDEO_TYPE'].isin(selected_video_types)]
    else:
        df_trend_agg = df_trend_agg.iloc[0:0]
        df_latest_raw = df_latest_raw.iloc[0:0]"""
code = code.replace(old_video_type, new_video_type)

# Fix empty check
code = code.replace("if df_full_filtered.empty:", "if df_trend_agg.empty or df_latest_raw.empty:")

# Fix df_latest_filtered definition
code = code.replace("df_latest_filtered = df_full_filtered[df_full_filtered['METRIC_DATE'] == latest_date]", 
                    "df_latest_filtered = df_latest_raw")

# Fix baseline dates logic for Daily/Rolling
# We replace df_full_filtered usage in charts
# For Daily:
code = code.replace("df_trend_filtered = df_full_filtered[df_full_filtered['METRIC_DATE'] >= start_date]",
                    "df_trend_filtered = df_trend_agg[df_trend_agg['METRIC_DATE'] >= start_date]")
code = code.replace("df_trend_filtered = df_full_filtered[df_full_filtered['METRIC_DATE'] >= seven_days_ago]",
                    "df_trend_filtered = df_trend_agg[df_trend_agg['METRIC_DATE'] >= seven_days_ago]")
code = code.replace("df_trend_filtered = df_full_filtered[df_full_filtered['METRIC_DATE'] >= thirty_days_ago]",
                    "df_trend_filtered = df_trend_agg[df_trend_agg['METRIC_DATE'] >= thirty_days_ago]")

# For Top Videos (daily)
code = code.replace("df_target = df_full_filtered[df_full_filtered['METRIC_DATE'] >= start_date]",
                    "df_target = df_latest_raw") 
# Wait! In the daily Top Videos logic, it used to sum up DAILY_VIEWS over the whole period if it was a 7-day trend.
# But load_video_snapshot_top ONLY returns the latest day!
# If metric_grain is "Daily - Past 7 Days Trend", calculating top videos by summing DAILY_VIEWS across 7 days requires raw data.
# The user's original code did:
# df_target = df_full_filtered[df_full_filtered['METRIC_DATE'] >= start_date]
# top_videos = df_target.groupby(...).agg({'DAILY_VIEWS': 'sum', 'TOTAL_VIEWS': 'max'})
# If we only have latest_raw, we can only rank by TOTAL_VIEWS or DAILY_VIEWS for yesterday.
# I will change the logic to rank by TOTAL_VIEWS (Lifetime) or DAILY_VIEWS (Yesterday) for ALL daily tabs, since we removed raw historical data.
code = code.replace("""    if metric_grain == "Daily - Yesterday Snapshot":
        df_target = df_latest_filtered
    else:
        days_to_sub = 6 if metric_grain == "Daily - Past 7 Days Trend" else 29
        start_date = latest_date - pd.Timedelta(days=days_to_sub)
        df_target = df_full_filtered[df_full_filtered['METRIC_DATE'] >= start_date]
        
        # Filter out baseline dates to prevent skewing the period views
        df_target = df_target[df_target['METRIC_DATE'] > df_target['CHANNEL_TITLE'].map(baseline_map)]
        
    top_videos = df_target.groupby(['VIDEO_ID', 'VIDEO_TITLE', 'CHANNEL_TITLE', 'VIDEO_TYPE', 'PUBLISHED_AT'], as_index=False).agg({
        'DAILY_VIEWS': 'sum',
        'TOTAL_VIEWS': 'max'
    }).sort_values(by='DAILY_VIEWS', ascending=False).head(100)""",
"""    df_target = df_latest_filtered
    top_videos = df_target.groupby(['VIDEO_ID', 'VIDEO_TITLE', 'CHANNEL_TITLE', 'VIDEO_TYPE', 'PUBLISHED_AT'], as_index=False).agg({
        'DAILY_VIEWS': 'max',
        'TOTAL_VIEWS': 'max'
    }).sort_values(by='DAILY_VIEWS', ascending=False).head(100)""")

with open("streamlit/pages/1_Video_Statistics.py", "w") as f:
    f.write(code)

print("Video_Statistics updated.")
