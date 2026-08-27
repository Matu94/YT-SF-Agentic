import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
from utils.data_loader import load_data


st.set_page_config(page_title="YT Metrics - Channel Info", layout="wide", initial_sidebar_state="expanded")

st.title("Channel Information")
st.markdown("Detailed breakdown of current statistics for a selected channel.")

try:
    df = load_data("RPT_CHANNEL_PERFORMANCE_DAILY")
except Exception as e:
    st.error(f"Failed to load data. Error: {e}")
    st.stop()


if df.empty:
    st.warning("No data available.")
    st.stop()
    
df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE'])

# --- Sidebar Filter ---
st.sidebar.header("Select Channel")

# Allow the user to simply select a channel to see its info
channels = df['CHANNEL_TITLE'].dropna().unique().tolist()
channels.sort()

# If there's no data, channels list might be empty
if not channels:
    st.info("No channels available.")
    st.stop()

selected_channel = st.sidebar.selectbox("Channel", channels)

# Filter to the selected channel
df_channel = df[df['CHANNEL_TITLE'] == selected_channel].copy()

if df_channel.empty:
    st.info("No data for this channel.")
else:
    # Get the latest row based on METRIC_DATE
    latest_data = df_channel.sort_values(by='METRIC_DATE', ascending=False).iloc[0]
    
    # --- KPIs ---
    st.subheader(f"{selected_channel} Overview")
    
    date_str = latest_data['METRIC_DATE'].date() if hasattr(latest_data['METRIC_DATE'], 'date') else latest_data['METRIC_DATE']
    st.markdown(f"**Data as of:** {date_str}")
    
    # Hierarchy/Grouping Info
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Organization", latest_data.get('ORGANIZATION', 'N/A'))
    with col2:
        st.metric("Team / Studio", latest_data.get('TEAM_STUDIO', 'N/A'))
    with col3:
        st.metric("Content Type", latest_data.get('CONTENT_TYPE', 'N/A'))
        
    st.divider()
    
    # Core Performance Metrics
    col4, col5, col6 = st.columns(3)
    
    # Handle cases where values might be null or missing
    subs = latest_data.get('TOTAL_SUBSCRIBERS')
    views = latest_data.get('TOTAL_VIEWS')
    videos = latest_data.get('TOTAL_VIDEOS')
    
    subs_formatted = f"{int(subs):,}" if pd.notnull(subs) else "N/A"
    views_formatted = f"{int(views):,}" if pd.notnull(views) else "N/A"
    videos_formatted = f"{int(videos):,}" if pd.notnull(videos) else "N/A"
    
    with col4:
        st.metric("Total Subscribers", subs_formatted)
    with col5:
        st.metric("Total Views", views_formatted)
    with col6:
        st.metric("Total Videos", videos_formatted)
