import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

# Set page config for a clean look
st.set_page_config(page_title="YT Metrics - Home", layout="wide", initial_sidebar_state="expanded")

# Connect to Snowflake using active session
session = get_active_session()

# Cache data loading
@st.cache_data(ttl=3600)
def load_channel_data():
    df = session.sql("SELECT * FROM MART.RPT_CHANNEL_PERFORMANCE_DAILY").to_pandas()
    return df

try:
    df = load_channel_data()
except Exception as e:
    st.error(f"Failed to load data from MART. Error: {e}")
    st.stop()

# Ensure METRIC_DATE is datetime
if not df.empty:
    df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE'])

# Welcome user
try:
    current_user = session.get_current_user()
    current_user = current_user.replace('"', '') if current_user else "User"
except Exception:
    current_user = "User"

st.title(f"Welcome, {current_user}! 👋")
st.markdown("Explore deep insights into your YouTube channel and video performance.")

st.divider()

if df.empty:
    st.warning("No data available in the data warehouse.")
    st.stop()

# 1. Latest Refresh Date & Status
latest_date = df['METRIC_DATE'].max()
st.info(f"🟢 **System Status:** Pipeline is healthy. Latest data refresh: **{latest_date.strftime('%Y-%m-%d')}**")

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

organizations = df['ORGANIZATION'].dropna().unique().tolist()
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
