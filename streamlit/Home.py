import streamlit as st
import altair as alt
import pandas as pd
from snowflake.snowpark.context import get_active_session

# Set page config for clean look and dark-mode compatibility
st.set_page_config(page_title="YT Metrics - Daily Views", layout="wide", initial_sidebar_state="expanded")

# Connect to Snowflake using active session (Native App Context)
session = get_active_session()

# Cache the data fetch to minimize warehouse usage
@st.cache_data(ttl=3600)
def load_data():
    # Load from the MART layer as dictated by Kimball guidelines
    df = session.sql("SELECT * FROM MART.RPT_CHANNEL_PERFORMANCE_DAILY").to_pandas()
    return df

st.title("YouTube Metrics: Daily Views")
st.markdown("Monitor daily view performance across organizations, studios, and channels.")

# Load Data
try:
    df = load_data()
except Exception as e:
    st.error(f"Failed to load data from MART.RPT_CHANNEL_PERFORMANCE_DAILY. Error: {e}")
    st.stop()

if df.empty:
    st.warning("No data available in MART.RPT_CHANNEL_PERFORMANCE_DAILY.")
    st.stop()

# Ensure METRIC_DATE is datetime for Altair compatibility
df['METRIC_DATE'] = pd.to_datetime(df['METRIC_DATE'])

# --- Sidebar Filters ---
st.sidebar.header("Filter Hierarchy")

# 1. Organization
organizations = df['ORGANIZATION'].dropna().unique().tolist()
organizations.sort()
selected_org = st.sidebar.selectbox("Select Organization", ["All"] + organizations)

if selected_org != "All":
    df_filtered = df[df['ORGANIZATION'] == selected_org]
else:
    df_filtered = df.copy()

# 2. Studio
if selected_org != "All":
    studios = df_filtered['TEAM_STUDIO'].dropna().unique().tolist()
    studios.sort()
    selected_studio = st.sidebar.selectbox("Select Studio", ["All"] + studios)
    if selected_studio != "All":
        df_filtered = df_filtered[df_filtered['TEAM_STUDIO'] == selected_studio]
else:
    # If no specific org, we can either disable or show all studios.
    studios = df_filtered['TEAM_STUDIO'].dropna().unique().tolist()
    studios.sort()
    selected_studio = st.sidebar.selectbox("Select Studio", ["All"] + studios)
    if selected_studio != "All":
        df_filtered = df_filtered[df_filtered['TEAM_STUDIO'] == selected_studio]

# 3. Channel
channels = df_filtered['CHANNEL_TITLE'].dropna().unique().tolist()
channels.sort()
selected_channel = st.sidebar.selectbox("Select Channel", ["All"] + channels)

if selected_channel != "All":
    df_filtered = df_filtered[df_filtered['CHANNEL_TITLE'] == selected_channel]

# --- Main Content ---
channel_label = selected_channel if selected_channel != 'All' else 'All Filtered Channels'
st.subheader(f"Daily Views: {channel_label}")

if df_filtered.empty:
    st.info("No data found for the selected filters.")
else:
    # Altair Chart optimized for Streamlit
    chart = alt.Chart(df_filtered).mark_line(point=True).encode(
        x=alt.X('METRIC_DATE:T', title='Date'),
        y=alt.Y('DAILY_VIEWS:Q', title='Daily Views'),
        color=alt.Color('CHANNEL_TITLE:N', title='Channel'),
        tooltip=['METRIC_DATE:T', 'CHANNEL_TITLE:N', 'DAILY_VIEWS:Q', 'TOTAL_VIEWS:Q', 'ORGANIZATION:N', 'TEAM_STUDIO:N']
    ).properties(
        height=500
    ).interactive()
    
    st.altair_chart(chart, use_container_width=True)
