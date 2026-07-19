import streamlit as st
import altair as alt
import pandas as pd
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="YT Metrics - Video Stats", layout="wide", initial_sidebar_state="expanded")

session = get_active_session()

@st.cache_data(ttl=3600)
def load_video_data():
    return session.sql("SELECT * FROM MART.RPT_VIDEO_PERFORMANCE_DAILY").to_pandas()

st.title("YouTube Metrics: Video Statistics")
st.markdown("Analyze video-level performance, filter by hierarchy, and explore top-performing content.")

try:
    df = load_video_data()
except Exception as e:
    st.error(f"Failed to load data from MART. Error: {e}")
    st.stop()

if df.empty:
    st.warning("No data available.")
    st.stop()

df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE'])

# Metric Toggle Placeholder
metric_grain = st.radio("Select Metric Grain", ["Daily", "Weekly"], horizontal=True)
if metric_grain == "Weekly":
    st.info("🚧 Weekly metrics are coming soon! Displaying daily metrics for now.")

# --- Sidebar Filters ---
st.sidebar.header("Hierarchy Filters")

# 1. Organizations
all_orgs = df['ORGANIZATION'].dropna().unique().tolist()
all_orgs.sort()
selected_orgs = st.sidebar.multiselect("Organizations", options=all_orgs, help="Leave empty to select all.")

if selected_orgs:
    df_filtered = df[df['ORGANIZATION'].isin(selected_orgs)]
else:
    df_filtered = df.copy()

# 2. Teams (Studios)
all_teams = df_filtered['TEAM_STUDIO'].dropna().unique().tolist()
all_teams.sort()
selected_teams = st.sidebar.multiselect("Teams (Studios)", options=all_teams, help="Filtered by selected Organizations. Leave empty to select all.")

if selected_teams:
    df_filtered = df_filtered[df_filtered['TEAM_STUDIO'].isin(selected_teams)]

# 3. Channels
all_channels = df_filtered['CHANNEL_TITLE'].dropna().unique().tolist()
all_channels.sort()
selected_channels = st.sidebar.multiselect("Channels", options=all_channels, help="Filtered by selected Teams. Leave empty to select all.")

if selected_channels:
    df_filtered = df_filtered[df_filtered['CHANNEL_TITLE'].isin(selected_channels)]

# 4. Video Type Filter
st.sidebar.header("Content Filters")
all_video_types = df['VIDEO_TYPE'].dropna().unique().tolist()
all_video_types.sort()

# By default, select all available types
selected_video_types = st.sidebar.multiselect("Video Types", options=all_video_types, default=all_video_types)

if selected_video_types:
    df_filtered = df_filtered[df_filtered['VIDEO_TYPE'].isin(selected_video_types)]
else:
    df_filtered = df_filtered.iloc[0:0] # empty if nothing is selected

# --- Main Content ---
st.divider()

if df_filtered.empty:
    st.warning("No data found for the selected filters.")
    st.stop()

# Aggregated Chart
st.subheader("Aggregated Views per Channel")
st.markdown("Shows the total sum of daily views for the selected channels and video types.")

# Group by channel
channel_agg = df_filtered.groupby('CHANNEL_TITLE', as_index=False)['DAILY_VIEWS'].sum()

chart = alt.Chart(channel_agg).mark_bar().encode(
    x=alt.X('CHANNEL_TITLE:N', title='Channel', sort='-y'),
    y=alt.Y('DAILY_VIEWS:Q', title='Period Views (Aggregated)'),
    color=alt.Color('CHANNEL_TITLE:N', legend=None),
    tooltip=[
        alt.Tooltip('CHANNEL_TITLE:N', title='Channel'),
        alt.Tooltip('DAILY_VIEWS:Q', title='Views')
    ]
).properties(
    height=450
).interactive()

st.altair_chart(chart, use_container_width=True)

st.divider()

# Top Performing Videos Data Table
st.subheader("Top Performing Videos")
st.markdown("Detailed breakdown of the highest-viewed individual videos based on your selection.")

# Aggregate by video over the selected time period
top_videos = df_filtered.groupby(['VIDEO_ID', 'VIDEO_TITLE', 'CHANNEL_TITLE', 'VIDEO_TYPE', 'PUBLISHED_AT'], as_index=False).agg({
    'DAILY_VIEWS': 'sum',
    'TOTAL_VIEWS': 'max'
}).sort_values(by='DAILY_VIEWS', ascending=False).head(100)

top_videos['PUBLISHED_AT'] = pd.to_datetime(top_videos['PUBLISHED_AT']).dt.strftime('%Y-%m-%d')

st.dataframe(
    top_videos.rename(columns={
        'VIDEO_TITLE': 'Video Title',
        'CHANNEL_TITLE': 'Channel',
        'VIDEO_TYPE': 'Type',
        'PUBLISHED_AT': 'Published Date',
        'DAILY_VIEWS': 'Period Views',
        'TOTAL_VIEWS': 'Lifetime Views'
    })[['Video Title', 'Channel', 'Type', 'Published Date', 'Period Views', 'Lifetime Views']], 
    hide_index=True, 
    use_container_width=True
)
