import streamlit as st
import altair as alt
import pandas as pd
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="YT Metrics - Channel Leaderboard", layout="wide", initial_sidebar_state="expanded")

session = get_active_session()
session.use_warehouse('YT_SF_REPORTING_WH')

@st.cache_data(ttl=3600)
def load_channel_performance():
    return session.sql("SELECT * FROM MART.RPT_CHANNEL_PERFORMANCE_DAILY").to_pandas()

st.title("📺 Channel Leaderboard")
st.markdown("Discover the top-performing channels across the network based on subscribers, views, and videos.")

try:
    df_channel = load_channel_performance()
except Exception as e:
    st.error(f"Failed to load data from MART. Error: {e}")
    st.stop()

if df_channel.empty:
    st.warning("No data available.")
    st.stop()

df_channel['METRIC_DATE'] = pd.to_datetime(df_channel['METRIC_DATE'])

# Combine data to create unified filters
all_orgs = sorted(df_channel['ORGANIZATION'].dropna().unique().tolist())
all_channels = sorted(df_channel['CHANNEL_TITLE'].dropna().unique().tolist())

# --- Sidebar Filters ---
st.sidebar.header("Hierarchy Filters")

selected_orgs = st.sidebar.multiselect("Organizations", options=all_orgs, help="Leave empty to select all.")

if selected_orgs:
    filtered_channels = sorted(df_channel[df_channel['ORGANIZATION'].isin(selected_orgs)]['CHANNEL_TITLE'].dropna().unique().tolist())
else:
    filtered_channels = all_channels

selected_channels = st.sidebar.multiselect("Channels", options=filtered_channels, help="Leave empty to select all.")

def apply_filters(df):
    res = df.copy()
    if selected_orgs:
        res = res[res['ORGANIZATION'].isin(selected_orgs)]
    if selected_channels:
        res = res[res['CHANNEL_TITLE'].isin(selected_channels)]
    return res

df_channel_filtered = apply_filters(df_channel)

# Filter to latest date so we rank correctly without double-counting history
latest_date = df_channel_filtered['METRIC_DATE'].max()
df_latest = df_channel_filtered[df_channel_filtered['METRIC_DATE'] == latest_date]

st.divider()

# --- Leaderboard Rendering Logic ---

tab1, tab2, tab3 = st.tabs(["👥 Most Subscribers", "👀 Most Views", "📹 Most Videos"])

def render_channel_leaderboard_tab(df_latest, metric_col, metric_label, tab_icon):
    if df_latest.empty:
        st.warning("No data found for the selected filters.")
        return

    # Top 3 KPIs
    top_3 = df_latest.nlargest(3, metric_col)
    
    col1, col2, col3 = st.columns(3)
    kpi_cols = [col1, col2, col3]
    medals = ["🥇", "🥈", "🥉"]
    
    for i in range(min(3, len(top_3))):
        row = top_3.iloc[i]
        with kpi_cols[i]:
            st.metric(
                label=f"{medals[i]} {row['CHANNEL_TITLE']}",
                value=f"{int(row[metric_col]):,}"
            )

    st.divider()
    
    st.subheader(f"Top 10 Channels by {metric_label}")
    # Horizontal Bar Chart for Top 10
    top_10 = df_latest.nlargest(10, metric_col).copy()
    
    chart = alt.Chart(top_10).mark_bar().encode(
        x=alt.X(f'{metric_col}:Q', title=metric_label),
        y=alt.Y('CHANNEL_TITLE:N', sort='-x', title='Channel'),
        color=alt.Color('CHANNEL_TITLE:N', title='Channel', legend=None),
        tooltip=[
            alt.Tooltip('CHANNEL_TITLE:N', title='Channel'),
            alt.Tooltip(f'{metric_col}:Q', title=metric_label, format=',')
        ]
    ).properties(
        height=400
    ).interactive()

    st.altair_chart(chart, use_container_width=True)
    
    st.divider()
    
    st.subheader(f"Top 50 Data Grid")
    display_cols = ['CHANNEL_TITLE', 'ORGANIZATION', 'METRIC_DATE', metric_col]
    rename_dict = {
        'CHANNEL_TITLE': 'Channel',
        'ORGANIZATION': 'Organization',
        'METRIC_DATE': 'Report Date',
        metric_col: metric_label
    }
    
    top_50 = df_latest.nlargest(50, metric_col).copy()
    display_df = top_50[display_cols].rename(columns=rename_dict)
    
    if 'Report Date' in display_df.columns:
        display_df['Report Date'] = pd.to_datetime(display_df['Report Date']).dt.strftime('%Y-%m-%d')
    
    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            metric_label: st.column_config.ProgressColumn(
                metric_label,
                help=f"Channel ranking by {metric_label.lower()}",
                format="%d",
                min_value=0,
                max_value=int(top_50[metric_col].max()) if not top_50.empty else 100,
            )
        }
    )

with tab1:
    render_channel_leaderboard_tab(df_latest, 'TOTAL_SUBSCRIBERS', 'Total Subscribers', '👥')

with tab2:
    render_channel_leaderboard_tab(df_latest, 'TOTAL_VIEWS', 'Total Views', '👀')

with tab3:
    render_channel_leaderboard_tab(df_latest, 'TOTAL_VIDEOS', 'Total Videos', '📹')
