"""Executive Overview & Demand Trends Component (Page 1)."""

from typing import Dict, Any, Optional
import pandas as pd
import plotly.express as px
import streamlit as st
from dashboard.data_service import (
    make_filter_key,
    query_hourly_demand,
    query_dow_demand,
    query_monthly_demand,
)
from dashboard.styles import get_plotly_layout_defaults


def render_demand_page(
    df: Optional[pd.DataFrame] = None,
    filter_spec: Optional[Dict[str, Any]] = None,
    **kwargs,
):
    """Render Page 1: Executive Overview & Demand Trends with 100% full-dataset SQL aggregations."""
    filter_key = make_filter_key(filter_spec)

    st.markdown("## 📊 Executive Overview & Demand Volume")
    st.markdown("---")

    c1, c2 = st.columns(2)

    # 1. Hourly Demand Profile across 24 Hours
    with c1:
        st.markdown("### 🔥 Hourly Trip Demand & Peak Hours")
        hourly_df = query_hourly_demand(filter_key, filter_spec)

        if not hourly_df.empty:
            fig_hour = px.bar(
                hourly_df,
                x="pickup_hour",
                y="trips",
                color="revenue",
                color_continuous_scale=["#0284C7", "#005BAE", "#38BDF8"],
                labels={
                    "pickup_hour": "Hour of Day (0 - 23)",
                    "trips": "Total Trips",
                    "revenue": "Total Revenue ($)",
                },
                title="Hourly Trip Demand Profile",
            )
            fig_hour.update_layout(**get_plotly_layout_defaults(), height=420)
            st.plotly_chart(
                fig_hour,
                use_container_width=True,
                config={"displayModeBar": False, "responsive": True},
            )

    # 2. Day of Week Volume Profile
    with c2:
        st.markdown("### 📅 Day of Week Volume Profile")
        dow_df = query_dow_demand(filter_key, filter_spec)

        if not dow_df.empty:
            dow_metric = st.radio(
                "Display Metric:",
                ["Normalized Daily Average (Trips / Day)", "Total Aggregate Trips"],
                horizontal=True,
                key="dow_view_metric",
            )
            y_col = "avg_daily_trips" if "Normalized" in dow_metric else "trips"
            y_label = (
                "Avg Trips / Calendar Date"
                if "Normalized" in dow_metric
                else "Total Trips"
            )
            chart_title = (
                "Normalized Average Daily Trips per Calendar Date"
                if "Normalized" in dow_metric
                else "Total Aggregated Trips by Weekday"
            )

            fig_dow = px.area(
                dow_df,
                x="pickup_day_of_week",
                y=y_col,
                markers=True,
                color_discrete_sequence=["#38BDF8"],
                hover_data={
                    "pickup_day_of_week": True,
                    "calendar_days": True,
                    "avg_daily_trips": ":,.0f",
                    "trips": ":,.0f",
                    "revenue": ":$,.2f",
                },
                labels={
                    "pickup_day_of_week": "Day of Week",
                    y_col: y_label,
                    "calendar_days": "Calendar Dates",
                    "avg_daily_trips": "Avg Trips/Day",
                    "trips": "Total Trips",
                    "revenue": "Total Revenue ($)",
                },
                title=chart_title,
            )
            fig_dow.update_layout(**get_plotly_layout_defaults(), height=370)
            st.plotly_chart(
                fig_dow,
                use_container_width=True,
                config={"displayModeBar": False, "responsive": True},
            )
            st.caption(
                "💡 **Calendar Normalization:** Total trips are influenced by uneven calendar date occurrences "
                "(e.g., 5 Thursdays vs 4 Mondays in January 2025). The normalized daily average removes date "
                "frequency skew for an accurate daily demand comparison."
            )

    # 3. Monthly Demand & Revenue Trend Profile across 2025 (Full Year Overview)
    monthly_df = query_monthly_demand(filter_key, filter_spec)

    if not monthly_df.empty:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🗓️ 2025 Monthly Demand & Revenue Trend Profile")

        m1, m2 = st.columns(2)
        with m1:
            fig_m_trips = px.bar(
                monthly_df,
                x="month_name",
                y="trips",
                color="trips",
                color_continuous_scale=["#005BAE", "#0284C7", "#38BDF8"],
                labels={"month_name": "Month (2025)", "trips": "Total Trips"},
                title="Monthly Trip Volume (2025)",
            )
            fig_m_trips.update_layout(**get_plotly_layout_defaults(), height=360)
            st.plotly_chart(
                fig_m_trips,
                use_container_width=True,
                config={"displayModeBar": False, "responsive": True},
            )

        with m2:
            fig_m_rev = px.line(
                monthly_df,
                x="month_name",
                y="revenue",
                markers=True,
                color_discrete_sequence=["#10B981"],
                labels={"month_name": "Month (2025)", "revenue": "Total Revenue ($)"},
                title="Monthly Gross Revenue Trend ($)",
            )
            fig_m_rev.update_layout(**get_plotly_layout_defaults(), height=360)
            st.plotly_chart(
                fig_m_rev,
                use_container_width=True,
                config={"displayModeBar": False, "responsive": True},
            )
