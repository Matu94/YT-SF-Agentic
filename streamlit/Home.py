import sys
import os
sys.path.append(os.path.dirname(__file__))

import streamlit as st
import pandas as pd
from utils.data_loader import load_data, get_current_user_name


# Set page config for a clean look
st.set_page_config(page_title="YT Metrics - Home", layout="wide", initial_sidebar_state="expanded")

try:
    df = load_data("RPT_CHANNEL_PERFORMANCE_DAILY")
except Exception as e:
    st.error(f"Failed to load data from MART. Error: {e}")
    st.stop()

# Ensure METRIC_DATE is datetime
if not df.empty:
    df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE'])

# Welcome user & Developer Info
current_user = get_current_user_name()
if current_user:
    st.title(f"Welcome, {current_user}! 👋")
else:
    st.title("Welcome! 👋")

st.markdown(
    "Explore deep insights into your YouTube channel and video performance.  \n"
    "**Created by Matu** — Connect on [LinkedIn](https://www.linkedin.com/in/matu94/) • [GitHub](https://github.com/Matu94)"
)

st.markdown("### 📊 What you can find here")
col_nav1, col_nav2, col_nav3 = st.columns(3)
with col_nav1:
    st.page_link("pages/1_Video_Statistics.py", label="Video Statistics", icon="📈")
    st.caption("Deep dive into video performance, views, and engagement metrics.")
with col_nav2:
    st.page_link("pages/2_Leaderboard.py", label="Leaderboard", icon="🏆")
    st.caption("Discover top performing videos and global channel rankings.")
with col_nav3:
    st.page_link("pages/3_Channel_Info.py", label="Channel Info", icon="ℹ️")
    st.caption("View detailed statistics, metadata, and trends for specific channels.")

# Sidebar Developer Links
st.sidebar.markdown("---")
st.sidebar.caption("**Developer Contact**")
st.sidebar.markdown("[LinkedIn](https://www.linkedin.com/in/matu94/)")
st.sidebar.markdown("[GitHub](https://github.com/Matu94)")

st.divider()

if df.empty:
    st.warning("No data available in the data warehouse.")
    st.stop()

# 1. Latest Data Available & Status
latest_date = df['METRIC_DATE'].max()
st.info(f"🟢 **System Status:** Pipeline is healthy. Latest data available: **{latest_date.strftime('%Y-%m-%d')}**")

st.divider()

# 2. KPI Metrics
st.subheader("Platform Overview")
# Filter to get latest data for KPIs to avoid duplicating metrics over time
df_latest = df[df['METRIC_DATE'] == latest_date]
total_subscribers = int(df_latest['TOTAL_SUBSCRIBERS'].sum())
total_views = int(df_latest['TOTAL_VIEWS'].sum())
total_channels = df_latest['CHANNEL_ID'].nunique()

col1, col2, col3 = st.columns(3)
col1.metric("Total Tracked Channels", f"{total_channels}")
col2.metric("Total Subscribers", f"{total_subscribers:,}")
col3.metric("Total Views", f"{total_views:,}")

st.divider()

# 3. Channel Directory using Expander
st.subheader("Available Channels Directory")

organizations = df_latest['ORGANIZATION'].dropna().unique().tolist()
organizations.sort()

for org in organizations:
    with st.expander(f"🏢 Organization: {org}"):
        df_org = df_latest[df_latest['ORGANIZATION'] == org]
        studios = df_org['TEAM_STUDIO'].dropna().unique().tolist()
        studios.sort()
        
        for studio in studios:
            st.markdown(f"**Studio:** {studio}")
            df_studio = df_org[df_org['TEAM_STUDIO'] == studio]
            
            # Select relevant columns and display as a dataframe
            channels = df_studio[['CHANNEL_TITLE', 'CONTENT_TYPE', 'TOTAL_SUBSCRIBERS']].drop_duplicates().sort_values('CHANNEL_TITLE')
            
            # Display channels
            st.dataframe(
                channels.rename(columns={
                    'CHANNEL_TITLE': 'Channel Name',
                    'CONTENT_TYPE': 'Content/Niche',
                    'TOTAL_SUBSCRIBERS': 'Subscribers'
                }), 
                hide_index=True, 
                use_container_width=True
            )
