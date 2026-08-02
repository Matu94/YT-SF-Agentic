import streamlit as st
import altair as alt
import pandas as pd
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="YT Metrics - Leaderboard", layout="wide", initial_sidebar_state="expanded")

session = get_active_session()
session.use_warehouse('YT_SF_REPORTING_WH')

@st.cache_data(ttl=3600)
def load_top_views():
    return session.sql("SELECT * FROM MART.RPT_TOP_VIDEO_BY_VIEWS").to_pandas()

@st.cache_data(ttl=3600)
def load_top_likes():
    return session.sql("SELECT * FROM MART.RPT_TOP_VIDEO_BY_LIKES").to_pandas()

@st.cache_data(ttl=3600)
def load_top_comments():
    return session.sql("SELECT * FROM MART.RPT_TOP_VIDEO_BY_COMMENTS").to_pandas()

@st.cache_data(ttl=3600)
def load_channel_performance():
    return session.sql("SELECT * FROM MART.RPT_CHANNEL_PERFORMANCE_DAILY").to_pandas()

st.title("🏆 Leaderboards")
st.markdown("Discover the most engaging content and top-performing channels across the network.")

try:
    df_views = load_top_views()
    df_likes = load_top_likes()
    df_comments = load_top_comments()
    df_channel = load_channel_performance()
except Exception as e:
    st.error(f"Failed to load data from MART. Error: {e}")
    st.stop()

if not df_channel.empty:
    df_channel['METRIC_DATE'] = pd.to_datetime(df_channel['METRIC_DATE'])

# Combine data to create unified filters
all_orgs = set()
all_channels = set()
for df in [df_views, df_likes, df_comments, df_channel]:
    if not df.empty:
        all_orgs.update(df['ORGANIZATION'].dropna().unique())
        all_channels.update(df['CHANNEL_TITLE'].dropna().unique())

all_orgs = sorted(list(all_orgs))
all_channels = sorted(list(all_channels))

# --- Sidebar Filters ---
st.sidebar.header("Hierarchy Filters")

selected_orgs = st.sidebar.multiselect("Organizations", options=all_orgs, help="Leave empty to select all.")

filtered_channels = set()
if selected_orgs:
    for df in [df_views, df_likes, df_comments, df_channel]:
        if not df.empty:
            filtered_channels.update(df[df['ORGANIZATION'].isin(selected_orgs)]['CHANNEL_TITLE'].dropna().unique())
else:
    filtered_channels = all_channels

filtered_channels = sorted(list(filtered_channels))
selected_channels = st.sidebar.multiselect("Channels", options=filtered_channels, help="Leave empty to select all.")

def apply_filters(df):
    if df.empty:
        return df
    res = df.copy()
    if selected_orgs:
        res = res[res['ORGANIZATION'].isin(selected_orgs)]
    if selected_channels:
        res = res[res['CHANNEL_TITLE'].isin(selected_channels)]
    return res

df_views_filtered = apply_filters(df_views)
df_likes_filtered = apply_filters(df_likes)
df_comments_filtered = apply_filters(df_comments)
df_channel_filtered = apply_filters(df_channel)

# --- Network KPIs ---
if not df_channel_filtered.empty:
    latest_date_channel = df_channel_filtered['METRIC_DATE'].max()
    latest_channel_data = df_channel_filtered[df_channel_filtered['METRIC_DATE'] == latest_date_channel]
    
    total_subs = latest_channel_data['TOTAL_SUBSCRIBERS'].sum()
    total_views = latest_channel_data['TOTAL_VIEWS'].sum()
    total_videos = latest_channel_data['TOTAL_VIDEOS'].sum()
    
    st.subheader("Network Overview")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("👥 Total Subscribers", f"{int(total_subs):,}")
    kpi2.metric("👀 Total Views", f"{int(total_views):,}")
    kpi3.metric("📹 Total Videos", f"{int(total_videos):,}")

st.divider()

# --- Leaderboard Rendering Logic ---

def render_video_leaderboard_tab(df, metric_col, metric_label, tab_icon):
    if df.empty:
        st.warning("No data found for the selected filters.")
        return

    # Top 3 KPIs
    top_3 = df.nlargest(3, metric_col)
    
    col1, col2, col3 = st.columns(3)
    kpi_cols = [col1, col2, col3]
    medals = ["🥇", "🥈", "🥉"]
    
    for i in range(min(3, len(top_3))):
        row = top_3.iloc[i]
        with kpi_cols[i]:
            st.metric(
                label=f"{medals[i]} {row['CHANNEL_TITLE']}",
                value=f"{int(row[metric_col]):,}",
                help=row['VIDEO_TITLE']
            )
            st.caption(f"{row['VIDEO_TITLE'][:50]}..." if len(row['VIDEO_TITLE']) > 50 else row['VIDEO_TITLE'])

    st.divider()
    
    st.subheader(f"Top 10 by {metric_label}")
    # Horizontal Bar Chart for Top 10
    top_10 = df.nlargest(10, metric_col).copy()
    # Create a short title for the chart to avoid overlapping
    top_10['SHORT_TITLE'] = top_10['VIDEO_TITLE'].apply(lambda x: x[:40] + '...' if len(str(x)) > 40 else x)
    
    chart = alt.Chart(top_10).mark_bar().encode(
        x=alt.X(f'{metric_col}:Q', title=metric_label),
        y=alt.Y('SHORT_TITLE:N', sort='-x', title='Video'),
        color=alt.Color('CHANNEL_TITLE:N', title='Channel'),
        tooltip=[
            alt.Tooltip('CHANNEL_TITLE:N', title='Channel'),
            alt.Tooltip('VIDEO_TITLE:N', title='Title'),
            alt.Tooltip(f'{metric_col}:Q', title=metric_label, format=',')
        ]
    ).properties(
        height=400
    ).interactive()

    st.altair_chart(chart, use_container_width=True)
    
    st.divider()
    
    st.subheader(f"Top 50 Data Grid")
    top_50 = df.nlargest(50, metric_col).copy()
    top_50['VIDEO_URL'] = "https://www.youtube.com/watch?v=" + top_50['VIDEO_ID']
    
    display_cols = ['VIDEO_TITLE', 'VIDEO_URL', 'CHANNEL_TITLE', 'ORGANIZATION', 'METRIC_DATE', metric_col]
    rename_dict = {
        'VIDEO_TITLE': 'Video Title',
        'VIDEO_URL': 'Watch Link',
        'CHANNEL_TITLE': 'Channel',
        'ORGANIZATION': 'Organization',
        'METRIC_DATE': 'Report Date',
        metric_col: metric_label
    }
    
    display_df = top_50[display_cols].rename(columns=rename_dict)
    
    if 'Report Date' in display_df.columns:
        display_df['Report Date'] = pd.to_datetime(display_df['Report Date']).dt.strftime('%Y-%m-%d')
    
    st.dataframe(
        display_df,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Watch Link": st.column_config.LinkColumn(
                "Watch Link",
                help="Click to open this video on YouTube",
                display_text="▶️ Open on YouTube"
            ),
            metric_label: st.column_config.ProgressColumn(
                metric_label,
                help=f"Video ranking by {metric_label.lower()}",
                format="%d",
                min_value=0,
                max_value=int(top_50[metric_col].max()) if not top_50.empty else 100,
            )
        }
    )

def render_channel_leaderboard_tab(df, metric_col, metric_label, tab_icon):
    if df.empty:
        st.warning("No data found for the selected filters.")
        return

    # Filter to latest date so we don't count all historical records
    latest_date = df['METRIC_DATE'].max()
    df_latest = df[df['METRIC_DATE'] == latest_date]

    if df_latest.empty:
        st.warning("No recent data found.")
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
    
    st.subheader(f"Top Channels by {metric_label}")
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
    
    st.subheader(f"Full Channel Ranking")
    display_cols = ['CHANNEL_TITLE', 'ORGANIZATION', 'METRIC_DATE', metric_col]
    rename_dict = {
        'CHANNEL_TITLE': 'Channel',
        'ORGANIZATION': 'Organization',
        'METRIC_DATE': 'Report Date',
        metric_col: metric_label
    }
    
    display_df = df_latest.sort_values(metric_col, ascending=False)[display_cols].rename(columns=rename_dict)
    
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
                max_value=int(df_latest[metric_col].max()) if not df_latest.empty else 100,
            )
        }
    )

# --- View Rendering ---

st.header("📹 Video Leaderboards")
v_tab1, v_tab2, v_tab3 = st.tabs(["👀 Most Viewed", "👍 Most Liked", "💬 Most Commented"])

with v_tab1:
    render_video_leaderboard_tab(df_views_filtered, 'TOTAL_VIEWS', 'Total Views', '👀')

with v_tab2:
    render_video_leaderboard_tab(df_likes_filtered, 'TOTAL_LIKES', 'Total Likes', '👍')

with v_tab3:
    render_video_leaderboard_tab(df_comments_filtered, 'TOTAL_COMMENTS', 'Total Comments', '💬')

st.divider()
st.header("📺 Channel Leaderboards")
c_tab1, c_tab2, c_tab3 = st.tabs(["👥 Most Subscribers", "👀 Most Views", "📹 Most Videos"])

with c_tab1:
    render_channel_leaderboard_tab(df_channel_filtered, 'TOTAL_SUBSCRIBERS', 'Total Subscribers', '👥')

with c_tab2:
    render_channel_leaderboard_tab(df_channel_filtered, 'TOTAL_VIEWS', 'Total Views', '👀')

with c_tab3:
    render_channel_leaderboard_tab(df_channel_filtered, 'TOTAL_VIDEOS', 'Total Videos', '📹')
