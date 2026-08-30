import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import altair as alt
import pandas as pd
from utils.data_loader import load_data


st.set_page_config(page_title="YT Metrics - Video Stats", layout="wide", initial_sidebar_state="expanded")

st.title("YouTube Metrics: Video Statistics")
st.markdown("Analyze video-level performance, filter by hierarchy, and explore top-performing content.")

options = [
    "Daily - Yesterday Snapshot", 
    "Daily - Past 7 Days Trend", 
    "Daily - Past 30 Days Trend", 
    "Rolling 7-Day Trend", 
    "Rolling 30-Day Trend"
]
metric_grain = st.radio("Select Metric Grain", options, horizontal=True)

with st.expander("ℹ️ Understanding Metric Calculations"):
    st.markdown("""
    **Daily Metrics**:
    - **Daily Delta Views**: The discrete number of views gained on a single specific calendar day.
    - $\Delta \text{Views} = \text{Total Views}_{\text{today}} - \text{Total Views}_{\text{yesterday}}$
    
    **Rolling Metrics**:
    - **Rolling Views**: The cumulative sum of daily views over the trailing $N$ days (7 or 30). Evaluated daily.
    - $\text{Rolling Views}(t) = \sum_{i=t-N+1}^t \Delta\text{Views}_i$
    """)

try:
    if metric_grain.startswith("Daily"):
        df = load_data("RPT_VIDEO_PERFORMANCE_DAILY")
    elif metric_grain == "Rolling 7-Day Trend":
        df = load_data("RPT_VIDEO_PERFORMANCE_ROLLING_7D")
    else:
        df = load_data("RPT_VIDEO_PERFORMANCE_ROLLING_30D")
except Exception as e:
    st.error(f"Failed to load data from MART. Error: {e}")
    st.stop()


if df.empty:
    st.warning("No data available.")
    st.stop()

df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE'])

latest_date = df['METRIC_DATE'].max()

# Keep a full history df for line charts if needed
df_full = df

if metric_grain == "Daily - Yesterday Snapshot":
    st.info(f"📅 Displaying discrete snapshot metrics for the latest available date: **{latest_date.strftime('%Y-%m-%d')}**")
elif metric_grain == "Daily - Past 7 Days Trend":
    st.info(f"📅 Displaying discrete daily view gains over the past 7 days up to **{latest_date.strftime('%Y-%m-%d')}**")
elif metric_grain == "Daily - Past 30 Days Trend":
    st.info(f"📅 Displaying discrete daily view gains over the past 30 days up to **{latest_date.strftime('%Y-%m-%d')}**")
elif metric_grain == "Rolling 7-Day Trend":
    st.info(f"📅 Displaying 7-day rolling metrics up to **{latest_date.strftime('%Y-%m-%d')}**")
else:
    st.info(f"📅 Displaying 30-day rolling metrics up to **{latest_date.strftime('%Y-%m-%d')}**")

st.success("💡 **Tip:** We've pre-selected the **top 5 performing channels** by views. Use the **Hierarchy Filters** in the sidebar to explore and compare other channels!")

# --- Sidebar Filters ---
st.sidebar.header("Hierarchy Filters")

# 1. Organizations
df_latest_for_filters = df_full[df_full['METRIC_DATE'] == latest_date]
all_orgs = df_latest_for_filters['ORGANIZATION'].dropna().unique().tolist()
all_orgs.sort()
selected_orgs = st.sidebar.multiselect("Organizations", options=all_orgs, help="Leave empty to select all.")

if selected_orgs:
    df_full_filtered = df_full[df_full['ORGANIZATION'].isin(selected_orgs)]
else:
    df_full_filtered = df_full

# 2. Teams (Studios)
df_latest_teams = df_full_filtered[df_full_filtered['METRIC_DATE'] == latest_date]
all_teams = df_latest_teams['TEAM_STUDIO'].dropna().unique().tolist()
all_teams.sort()
selected_teams = st.sidebar.multiselect("Teams (Studios)", options=all_teams, help="Filtered by selected Organizations. Leave empty to select all.")

if selected_teams:
    df_full_filtered = df_full_filtered[df_full_filtered['TEAM_STUDIO'].isin(selected_teams)]

# 3. Channels
df_latest_channels = df_full_filtered[df_full_filtered['METRIC_DATE'] == latest_date]
all_channels = df_latest_channels['CHANNEL_TITLE'].dropna().unique().tolist()
all_channels.sort()

if metric_grain.startswith("Daily"):
    sort_metric = 'DAILY_VIEWS'
elif metric_grain == "Rolling 7-Day Trend":
    sort_metric = 'ROLLING_7D_VIEWS'
else:
    sort_metric = 'ROLLING_30D_VIEWS'

if not df_latest_channels.empty and sort_metric in df_latest_channels.columns:
    top_5_channels = df_latest_channels.groupby('CHANNEL_TITLE')[sort_metric].sum().nlargest(5).index.tolist()
else:
    top_5_channels = all_channels[:5]

selected_channels = st.sidebar.multiselect("Channels", options=all_channels, default=top_5_channels, help="Filtered by selected Teams. Leave empty to clear all data.")

if selected_channels:
    df_full_filtered = df_full_filtered[df_full_filtered['CHANNEL_TITLE'].isin(selected_channels)]
else:
    df_full_filtered = df_full_filtered.iloc[0:0]

# 4. Video Type Filter (Conditional based on presence in data)
if 'VIDEO_TYPE' in df_full.columns:
    st.sidebar.header("Content Filters")
    df_latest_types = df_full_filtered[df_full_filtered['METRIC_DATE'] == latest_date]
    all_video_types = df_latest_types['VIDEO_TYPE'].dropna().unique().tolist()
    all_video_types.sort()
    
    selected_video_types = st.sidebar.multiselect("Video Types", options=all_video_types, default=all_video_types)
    
    if selected_video_types:
        df_full_filtered = df_full_filtered[df_full_filtered['VIDEO_TYPE'].isin(selected_video_types)]
    else:
        df_full_filtered = df_full_filtered.iloc[0:0] 

# --- Main Content ---
st.divider()

if df_full_filtered.empty:
    st.warning("No data found for the selected filters.")
    st.stop()

# For calculations that only make sense on the latest date (like total current views or daily sum)
df_latest_filtered = df_full_filtered[df_full_filtered['METRIC_DATE'] == latest_date]

# Calculate baseline dates for channels to prevent "onboarding spikes" in trend aggregations
baseline_dates = df_full.groupby('CHANNEL_TITLE', as_index=False)['METRIC_DATE'].min()
baseline_dates.rename(columns={'METRIC_DATE': 'BASELINE_DATE'}, inplace=True)

if metric_grain == "Daily - Yesterday Snapshot":
    st.subheader("Aggregated Views per Channel")
    st.markdown("Shows the total sum of daily views for the selected channels and video types on the snapshot date.")

    channel_agg = df_latest_filtered.groupby('CHANNEL_TITLE', as_index=False).agg({
        'DAILY_VIEWS': 'sum',
        'VIDEO_ID': 'nunique'
    }).rename(columns={'VIDEO_ID': 'VIDEO_COUNT'})

    chart = alt.Chart(channel_agg).mark_bar().encode(
        x=alt.X('CHANNEL_TITLE:N', title='Channel', sort='-y'),
        y=alt.Y('DAILY_VIEWS:Q', title='Period Views (Aggregated)'),
        color=alt.Color('CHANNEL_TITLE:N', legend=None),
        tooltip=[
            alt.Tooltip('CHANNEL_TITLE:N', title='Channel'),
            alt.Tooltip('DAILY_VIEWS:Q', title='Period Views (Aggregated)'),
            alt.Tooltip('VIDEO_COUNT:Q', title='Video Count')
        ]
    ).properties(
        height=450
    ).interactive()

    st.altair_chart(chart, use_container_width=True)

elif metric_grain in ["Daily - Past 7 Days Trend", "Daily - Past 30 Days Trend"]:
    days_to_sub = 6 if metric_grain == "Daily - Past 7 Days Trend" else 29
    start_date = latest_date - pd.Timedelta(days=days_to_sub)
    
    st.subheader(f"Discrete Daily Views Trend ({days_to_sub + 1} Days)")
    st.markdown(f"Displays the day-by-day discrete view gains over the past {days_to_sub + 1} days.")
    
    df_trend_filtered = df_full_filtered[df_full_filtered['METRIC_DATE'] >= start_date]
    
    # Filter out baseline dates
    df_trend_filtered = df_trend_filtered.merge(baseline_dates, on='CHANNEL_TITLE')
    df_trend_filtered = df_trend_filtered[df_trend_filtered['METRIC_DATE'] > df_trend_filtered['BASELINE_DATE']]
    
    trend_data = df_trend_filtered.groupby(['METRIC_DATE', 'CHANNEL_TITLE'], as_index=False).agg({
        'DAILY_VIEWS': 'sum'
    })
    
    line_chart = alt.Chart(trend_data).mark_line(point=True).encode(
        x=alt.X('METRIC_DATE:T', title='Date'),
        y=alt.Y('DAILY_VIEWS:Q', title='Daily Views'),
        color=alt.Color('CHANNEL_TITLE:N', title='Channel'),
        tooltip=[
            alt.Tooltip('CHANNEL_TITLE:N', title='Channel'),
            alt.Tooltip('METRIC_DATE:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('DAILY_VIEWS:Q', title='Daily Views', format=',')
        ]
    ).properties(
        height=450
    ).interactive()

    st.altair_chart(line_chart, use_container_width=True)

elif metric_grain == "Rolling 7-Day Trend":
    st.subheader("Rolling 7-Day Views Trend")
    st.markdown("Displays the 7-day rolling sum of views over the past 7 days for the selected channels.")
    
    seven_days_ago = latest_date - pd.Timedelta(days=6)
    df_trend_filtered = df_full_filtered[df_full_filtered['METRIC_DATE'] >= seven_days_ago]
    
    # Filter out baseline dates
    df_trend_filtered = df_trend_filtered.merge(baseline_dates, on='CHANNEL_TITLE')
    df_trend_filtered = df_trend_filtered[df_trend_filtered['METRIC_DATE'] > df_trend_filtered['BASELINE_DATE']]
    
    trend_data = df_trend_filtered.groupby(['METRIC_DATE', 'CHANNEL_TITLE'], as_index=False).agg({
        'ROLLING_7D_VIEWS': 'sum'
    })
    
    line_chart = alt.Chart(trend_data).mark_line(point=True).encode(
        x=alt.X('METRIC_DATE:T', title='Date'),
        y=alt.Y('ROLLING_7D_VIEWS:Q', title='Rolling 7-Day Views'),
        color=alt.Color('CHANNEL_TITLE:N', title='Channel'),
        tooltip=[
            alt.Tooltip('CHANNEL_TITLE:N', title='Channel'),
            alt.Tooltip('METRIC_DATE:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('ROLLING_7D_VIEWS:Q', title='Rolling 7-Day Views', format=',')
        ]
    ).properties(
        height=450
    ).interactive()

    st.altair_chart(line_chart, use_container_width=True)

else:
    st.subheader("Rolling 30-Day Views Trend")
    st.markdown("Displays the 30-day rolling sum of views over the past 30 days for the selected channels.")
    
    thirty_days_ago = latest_date - pd.Timedelta(days=29)
    df_trend_filtered = df_full_filtered[df_full_filtered['METRIC_DATE'] >= thirty_days_ago]
    
    # Filter out baseline dates
    df_trend_filtered = df_trend_filtered.merge(baseline_dates, on='CHANNEL_TITLE')
    df_trend_filtered = df_trend_filtered[df_trend_filtered['METRIC_DATE'] > df_trend_filtered['BASELINE_DATE']]
    
    trend_data = df_trend_filtered.groupby(['METRIC_DATE', 'CHANNEL_TITLE'], as_index=False).agg({
        'ROLLING_30D_VIEWS': 'sum'
    })
    
    line_chart = alt.Chart(trend_data).mark_line(point=True).encode(
        x=alt.X('METRIC_DATE:T', title='Date'),
        y=alt.Y('ROLLING_30D_VIEWS:Q', title='Rolling 30-Day Views'),
        color=alt.Color('CHANNEL_TITLE:N', title='Channel'),
        tooltip=[
            alt.Tooltip('CHANNEL_TITLE:N', title='Channel'),
            alt.Tooltip('METRIC_DATE:T', title='Date', format='%Y-%m-%d'),
            alt.Tooltip('ROLLING_30D_VIEWS:Q', title='Rolling 30-Day Views', format=',')
        ]
    ).properties(
        height=450
    ).interactive()

    st.altair_chart(line_chart, use_container_width=True)


st.divider()

st.subheader("Top Performing Videos")
st.markdown("Detailed breakdown of the highest-viewed individual videos based on your selection.")

if metric_grain.startswith("Daily"):
    # For daily trend or snapshot, sum up the daily views over the requested timeframe
    if metric_grain == "Daily - Yesterday Snapshot":
        df_target = df_latest_filtered
    else:
        days_to_sub = 6 if metric_grain == "Daily - Past 7 Days Trend" else 29
        start_date = latest_date - pd.Timedelta(days=days_to_sub)
        df_target = df_full_filtered[df_full_filtered['METRIC_DATE'] >= start_date]
        
        # Filter out baseline dates to prevent skewing the period views
        df_target = df_target.merge(baseline_dates, on='CHANNEL_TITLE')
        df_target = df_target[df_target['METRIC_DATE'] > df_target['BASELINE_DATE']]
        
    top_videos = df_target.groupby(['VIDEO_ID', 'VIDEO_TITLE', 'CHANNEL_TITLE', 'VIDEO_TYPE', 'PUBLISHED_AT'], as_index=False).agg({
        'DAILY_VIEWS': 'sum',
        'TOTAL_VIEWS': 'max'
    }).sort_values(by='DAILY_VIEWS', ascending=False).head(100)
    
    top_videos['PUBLISHED_AT'] = pd.to_datetime(top_videos['PUBLISHED_AT']).dt.strftime('%Y-%m-%d')
    top_videos['VIDEO_URL'] = "https://www.youtube.com/watch?v=" + top_videos['VIDEO_ID']
    
    display_df = top_videos.rename(columns={
        'VIDEO_TITLE': 'Video Title',
        'VIDEO_URL': 'Watch Link',
        'CHANNEL_TITLE': 'Channel',
        'VIDEO_TYPE': 'Type',
        'PUBLISHED_AT': 'Published Date',
        'DAILY_VIEWS': 'Period Views',
        'TOTAL_VIEWS': 'Lifetime Views'
    })[['Video Title', 'Watch Link', 'Channel', 'Type', 'Published Date', 'Period Views', 'Lifetime Views']]

elif metric_grain == "Rolling 7-Day Trend":
    cols_to_group = ['VIDEO_ID', 'VIDEO_TITLE', 'CHANNEL_TITLE']
    if 'VIDEO_TYPE' in df_latest_filtered.columns:
        cols_to_group.append('VIDEO_TYPE')
    if 'PUBLISHED_AT' in df_latest_filtered.columns:
        cols_to_group.append('PUBLISHED_AT')
        
    top_videos = df_latest_filtered.groupby(cols_to_group, as_index=False).agg({
        'ROLLING_7D_VIEWS': 'max'
    }).sort_values(by='ROLLING_7D_VIEWS', ascending=False).head(100)
    
    if 'PUBLISHED_AT' in top_videos.columns:
        top_videos['PUBLISHED_AT'] = pd.to_datetime(top_videos['PUBLISHED_AT']).dt.strftime('%Y-%m-%d')
        
    top_videos['VIDEO_URL'] = "https://www.youtube.com/watch?v=" + top_videos['VIDEO_ID']
    
    rename_dict = {
        'VIDEO_TITLE': 'Video Title',
        'VIDEO_URL': 'Watch Link',
        'CHANNEL_TITLE': 'Channel',
        'ROLLING_7D_VIEWS': 'Rolling 7-Day Views'
    }
    
    display_cols = ['Video Title', 'Watch Link', 'Channel']
    
    if 'VIDEO_TYPE' in top_videos.columns:
        rename_dict['VIDEO_TYPE'] = 'Type'
        display_cols.append('Type')
    if 'PUBLISHED_AT' in top_videos.columns:
        rename_dict['PUBLISHED_AT'] = 'Published Date'
        display_cols.append('Published Date')
        
    display_cols.append('Rolling 7-Day Views')
    
    display_df = top_videos.rename(columns=rename_dict)[display_cols]

else:
    cols_to_group = ['VIDEO_ID', 'VIDEO_TITLE', 'CHANNEL_TITLE']
    if 'VIDEO_TYPE' in df_latest_filtered.columns:
        cols_to_group.append('VIDEO_TYPE')
    if 'PUBLISHED_AT' in df_latest_filtered.columns:
        cols_to_group.append('PUBLISHED_AT')
        
    top_videos = df_latest_filtered.groupby(cols_to_group, as_index=False).agg({
        'ROLLING_30D_VIEWS': 'max'
    }).sort_values(by='ROLLING_30D_VIEWS', ascending=False).head(100)
    
    if 'PUBLISHED_AT' in top_videos.columns:
        top_videos['PUBLISHED_AT'] = pd.to_datetime(top_videos['PUBLISHED_AT']).dt.strftime('%Y-%m-%d')
        
    top_videos['VIDEO_URL'] = "https://www.youtube.com/watch?v=" + top_videos['VIDEO_ID']
    
    rename_dict = {
        'VIDEO_TITLE': 'Video Title',
        'VIDEO_URL': 'Watch Link',
        'CHANNEL_TITLE': 'Channel',
        'ROLLING_30D_VIEWS': 'Rolling 30-Day Views'
    }
    
    display_cols = ['Video Title', 'Watch Link', 'Channel']
    
    if 'VIDEO_TYPE' in top_videos.columns:
        rename_dict['VIDEO_TYPE'] = 'Type'
        display_cols.append('Type')
    if 'PUBLISHED_AT' in top_videos.columns:
        rename_dict['PUBLISHED_AT'] = 'Published Date'
        display_cols.append('Published Date')
        
    display_cols.append('Rolling 30-Day Views')
    
    display_df = top_videos.rename(columns=rename_dict)[display_cols]


st.dataframe(
    display_df, 
    hide_index=True, 
    use_container_width=True,
    column_config={
        "Watch Link": st.column_config.LinkColumn(
            "Watch Link",
            help="Click to open this video on YouTube",
            display_text="▶️ Open on YouTube"
        )
    }
)
