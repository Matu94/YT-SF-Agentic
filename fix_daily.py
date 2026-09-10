import sys

with open("streamlit/pages/1_Video_Statistics.py", "r") as f:
    code = f.read()

bad_block = """if metric_grain.startswith("Daily"):
    # For daily trend or snapshot, sum up the daily views over the requested timeframe
    if metric_grain == "Daily - Yesterday Snapshot":
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
    }).sort_values(by='DAILY_VIEWS', ascending=False).head(100)"""

good_block = """if metric_grain.startswith("Daily"):
    # Since we push down the aggregations and only load the latest day raw data for Top Videos,
    # we rank by yesterday's DAILY_VIEWS or Lifetime TOTAL_VIEWS.
    df_target = df_latest_filtered
        
    top_videos = df_target.groupby(['VIDEO_ID', 'VIDEO_TITLE', 'CHANNEL_TITLE', 'VIDEO_TYPE', 'PUBLISHED_AT'], as_index=False).agg({
        'DAILY_VIEWS': 'max',
        'TOTAL_VIEWS': 'max'
    }).sort_values(by='DAILY_VIEWS', ascending=False).head(100)"""

code = code.replace(bad_block, good_block)

with open("streamlit/pages/1_Video_Statistics.py", "w") as f:
    f.write(code)

print("Daily block fixed")
