import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from pathlib import Path

st.set_page_config(
    page_title="Skin Essentials by Her - Analytics Dashboard",
    page_icon="💄",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).parent


@st.cache_data
def load_data():
    """Load data from JSON reports - automatically finds latest report"""
    # Find the latest report file for this website
    report_files = list(DATA_DIR.glob("data_report_skinessentialsbyher.com_*.json"))
    if report_files:
        # Sort by modification time and get the latest
        latest_file = max(report_files, key=lambda p: p.stat().st_mtime)
        with open(latest_file, "r") as f:
            return json.load(f), latest_file.name
    return None, None


data, data_file = load_data()

if data is None:
    st.error("No data available. Please run the data analyst first.")
    st.stop()

st.title("💄 Skin Essentials by Her - Analytics Dashboard")
st.markdown(
    f"**Data Source:** {data_file} | **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)

# Sidebar - Connector Status
st.sidebar.title("🔌 Connector Status")
st.sidebar.markdown("---")

# Check connector configurations - support both local (.env) and Streamlit Cloud (secrets)
import os
import sys


def get_secret(key, default=None):
    """Get secret from Streamlit Cloud secrets or local .env"""
    # Try Streamlit Cloud secrets first
    try:
        if hasattr(st, "secrets"):
            if key in st.secrets:
                return st.secrets[key]
            # If we have any secrets, we're on cloud
            return default
    except:
        pass
    # Fall back to .env for local development
    from dotenv import load_dotenv

    load_dotenv(DATA_DIR / ".env")
    return os.getenv(key, default)


def is_cloud_deployed():
    """Check if running on Streamlit Cloud"""
    try:
        # If secrets exist and has content, we're on cloud
        if hasattr(st, "secrets") and len(st.secrets) > 0:
            return True
    except:
        pass
    return False


gsc_creds = get_secret("GSC_CREDENTIALS_PATH", "service-account.json")
ga4_creds = get_secret("GA4_CREDENTIALS_PATH", "service-account.json")
ga4_prop_id = get_secret("GA4_PROPERTY_ID", "520220708")
meta_token = get_secret("META_ACCESS_TOKEN", "")
meta_page = get_secret("META_PAGE_ID", "101807912975262")

# Check if we're on Streamlit Cloud (secrets available) or local (file exists)
on_cloud = is_cloud_deployed()

st.sidebar.markdown("### Google Search Console")
if on_cloud:
    st.sidebar.success("✅ Connected (Cloud)")
elif Path(DATA_DIR / gsc_creds).exists():
    st.sidebar.success(f"✅ Connected: {gsc_creds}")
else:
    st.sidebar.warning("⚠️ Demo Mode (no credentials)")

st.sidebar.markdown("### Google Analytics 4")
if on_cloud:
    st.sidebar.success(f"✅ Connected (Cloud): Property {ga4_prop_id}")
elif ga4_prop_id:
    st.sidebar.success(f"✅ Connected: Property {ga4_prop_id}")
else:
    st.sidebar.warning("⚠️ Demo Mode (no credentials)")

st.sidebar.markdown("### Meta/Facebook")
if on_cloud:
    st.sidebar.success(f"✅ Connected (Cloud): Page {meta_page}")
elif meta_token and meta_page:
    st.sidebar.success(f"✅ Connected: Page {meta_page}")
else:
    st.sidebar.warning("⚠️ Token missing - needs refresh")

st.sidebar.markdown("---")
st.sidebar.markdown("### Configuration")
st.sidebar.code(f"""
GSC: {gsc_creds or "Not set"}
GA4 Property ID: {ga4_prop_id or "Not set"}
Meta Page: {meta_page or "Not set"}
""")

# Overall Score Section
st.markdown("## 📊 Overall Performance Score")
scores = data.get("scores", {})
overall = scores.get("overall", 0)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Overall Score", f"{overall:.1f}/100", delta_color="normal")
with col2:
    st.metric("Search Visibility", f"{scores.get('search_visibility', 0):.1f}/100")
with col3:
    st.metric("GA4 Performance", f"{scores.get('ga4_performance', 0):.1f}/100")
with col4:
    st.metric("Meta Performance", f"{scores.get('meta_performance', 0):.1f}/100")
with col5:
    st.metric("Technical Health", f"{scores.get('technical_health', 0):.1f}/100")

# Score breakdown chart
fig_scores = go.Figure(
    go.Indicator(
        mode="gauge+number",
        value=overall,
        title={"text": "Overall Performance"},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#1f77b4"},
            "steps": [
                {"range": [0, 50], "color": "#ffccc7"},
                {"range": [50, 75], "color": "#fff1b8"},
                {"range": [75, 100], "color": "#d9f7be"},
            ],
        },
    )
)
st.plotly_chart(fig_scores, use_container_width=True)

st.markdown("---")

# Channel Tabs
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "🔍 Search Console (GSC)",
        "📊 Google Analytics 4",
        "📱 Meta Insights",
        "📋 Recommendations",
    ]
)

with tab1:
    st.header("🔍 Google Search Console - SEO Performance")
    channels = data.get("channels", {})
    gsc = channels.get("gsc", {})

    # GSC Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Clicks", gsc.get("total_clicks", 0))
    with col2:
        st.metric("Total Impressions", gsc.get("total_impressions", 0))
    with col3:
        st.metric("Average CTR", f"{gsc.get('average_ctr', 0) * 100:.2f}%")
    with col4:
        st.metric("Avg Position", f"{gsc.get('average_position', 0):.1f}")

    # Top Rankings
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Top 3 Rankings", gsc.get("top_3_rankings", 0))
    with col2:
        st.metric("Positions 4-10", gsc.get("positions_4_10", 0))

    # Top Queries Table
    st.markdown("### 🔑 Top Performing Queries")
    top_queries = gsc.get("top_queries", [])
    if top_queries:
        queries_df = pd.DataFrame(
            [
                {
                    "Query": q.get("keys", [""])[0] if q.get("keys") else "",
                    "Clicks": q.get("clicks", 0),
                    "Impressions": q.get("impressions", 0),
                    "CTR": f"{q.get('ctr', 0) * 100:.2f}%",
                    "Position": f"{q.get('position', 0):.1f}",
                }
                for q in top_queries
            ]
        )
        st.dataframe(queries_df, use_container_width=True, hide_index=True)

        # Query Performance Chart
        fig_queries = px.bar(
            queries_df.head(5),
            x="Query",
            y="Clicks",
            title="Top 5 Queries by Clicks",
            color="Clicks",
            color_continuous_scale="Greens",
        )
        st.plotly_chart(fig_queries, use_container_width=True)

    st.markdown("### 💡 GSC Insights")
    st.info(f"""
    - **{gsc.get("total_clicks", 0)} clicks** from **{gsc.get("total_impressions", 0)} impressions** in this period
    - Average ranking position: **{gsc.get("average_position", 0):.1f}**
    - **{gsc.get("top_3_rankings", 0)} queries** ranking in top 3 positions
    """)

with tab2:
    st.header("📊 Google Analytics 4 - Web Analytics")
    ga4 = channels.get("ga4", {})

    # GA4 Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Sessions", ga4.get("total_sessions", 0))
    with col2:
        st.metric("Users", ga4.get("total_users", 0))
    with col3:
        st.metric("Pageviews", ga4.get("total_pageviews", 0))
    with col4:
        st.metric("Bounce Rate", f"{ga4.get('bounce_rate', 0) * 100:.1f}%")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Conversions", ga4.get("conversions", 0))
    with col2:
        st.metric("Conversion Rate", f"{ga4.get('conversion_rate', 0) * 100:.2f}%")
    with col3:
        st.metric("Avg Session Duration", f"{ga4.get('avg_session_duration', 0):.0f}s")

    # Device Breakdown
    st.markdown("### 📱 Device Breakdown")
    device_data = ga4.get("device_breakdown", {})
    if device_data:
        device_df = pd.DataFrame(
            [{"Device": k.capitalize(), "Sessions": v} for k, v in device_data.items()]
        )
        fig_device = px.pie(
            device_df,
            values="Sessions",
            names="Device",
            title="Sessions by Device Type",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig_device, use_container_width=True)

    # Traffic Sources
    st.markdown("### 🌐 Traffic Sources")
    source_data = ga4.get("source_breakdown", {})
    if source_data:
        source_df = pd.DataFrame(
            [{"Source": k, "Sessions": v} for k, v in source_data.items()]
        ).sort_values("Sessions", ascending=False)

        fig_source = px.bar(
            source_df.head(7),
            x="Source",
            y="Sessions",
            title="Traffic by Source",
            color="Sessions",
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig_source, use_container_width=True)

    st.markdown("### 💡 GA4 Insights")
    st.info(f"""
    - **{ga4.get("total_sessions", 0)} sessions** from **{ga4.get("total_users", 0)} unique users**
    - Bounce rate: **{ga4.get("bounce_rate", 0) * 100:.1f}%** (high - needs improvement)
    - Conversion rate: **{ga4.get("conversion_rate", 0) * 100:.2f}%**
    - Top device: **{max(device_data, key=device_data.get) if device_data else "N/A"}**
    """)

with tab3:
    st.header("📱 Meta/Facebook Insights")
    meta = channels.get("meta", {})

    if meta and meta.get("total_impressions", 0) > 0:
        # Meta Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Impressions", f"{meta.get('total_impressions', 0):,}")
        with col2:
            st.metric("Engaged Users", f"{meta.get('total_engaged_users', 0):,}")
        with col3:
            st.metric("Page Fans", f"{meta.get('total_fans', 0):,}")
        with col4:
            st.metric("Engagement Rate", f"{meta.get('engagement_rate', 0) * 100:.2f}%")

        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                "Avg Daily Impressions", f"{meta.get('avg_daily_impressions', 0):,}"
            )
        with col2:
            st.metric("Avg Daily Engaged", f"{meta.get('avg_daily_engaged', 0):,}")

        # Recent Posts
        st.markdown("### 📝 Recent Posts Performance")
        recent_posts = meta.get("recent_posts", [])
        if recent_posts:
            posts_df = pd.DataFrame(
                [
                    {
                        "Message": p.get("message", "")[:50] + "..."
                        if len(p.get("message", "")) > 50
                        else p.get("message", ""),
                        "Date": p.get("created_time", "")[:10],
                        "Likes": p.get("likes", 0),
                        "Comments": p.get("comments", 0),
                        "Shares": p.get("shares", 0),
                        "Total Engagement": p.get("total_engagement", 0),
                    }
                    for p in recent_posts[:10]
                ]
            )
            st.dataframe(posts_df, use_container_width=True, hide_index=True)

            # Engagement Chart
            fig_posts = px.bar(
                posts_df,
                x="Date",
                y="Total Engagement",
                title="Post Engagement Over Time",
                color="Total Engagement",
                color_continuous_scale="Oranges",
            )
            st.plotly_chart(fig_posts, use_container_width=True)

        st.markdown("### 💡 Meta Insights")
        st.info(f"""
        - **{meta.get("total_impressions", 0):,} total impressions** with **{meta.get("engagement_rate", 0) * 100:.2f}%** engagement rate
        - **{meta.get("total_fans", 0):,} page followers**
        - Average of **{meta.get("avg_daily_impressions", 0):,} impressions** per day
        """)
    else:
        st.warning(
            "⚠️ Meta token has expired. Please refresh the access token in .env to fetch live data."
        )
        st.markdown("""
        ### To refresh Meta token:
        1. Go to Facebook Developers -> My Apps
        2. Navigate to Tools -> Graph API Explorer
        3. Generate a new User Token with required permissions
        4. Update META_ACCESS_TOKEN in .env file
        """)

with tab4:
    st.header("📋 Recommendations")
    recommendations = data.get("recommendations", [])

    if recommendations:
        for i, rec in enumerate(recommendations):
            priority = rec.get("priority", "Medium")
            priority_color = (
                "🔴" if priority == "High" else ("🟡" if priority == "Medium" else "🟢")
            )

            with st.expander(
                f"{priority_color} {priority} Priority - {rec.get('title', 'Recommendation')}"
            ):
                st.markdown(f"**Channel:** {rec.get('channel', 'N/A')}")
                st.markdown(f"**Description:** {rec.get('description', '')}")
                st.markdown(
                    f"**Impact:** {rec.get('impact', 'N/A')} | **Effort:** {rec.get('effort', 'N/A')}"
                )
    else:
        st.info("No recommendations available")

    # Summary
    st.markdown("### 📝 Executive Summary")
    summary = data.get("summary", "")
    st.markdown(summary)

# Footer
st.markdown("---")
st.markdown(
    f"""
<div style='text-align: center; color: gray;'>
    <p>📊 Analytics Dashboard for skinessentialsbyher.com</p>
    <p>Report Period: February 23-28, 2026</p>
    <p>Data Sources: Google Search Console (Live) | Google Analytics 4 (Live) | Meta (Token Expired)</p>
    <p>Generated by Data Analyst Agent | For internal use only</p>
</div>
""",
    unsafe_allow_html=True,
)
