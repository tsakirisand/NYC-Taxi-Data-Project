"""Executive Overview & Demand Trends Component (Page 1)."""

import pandas as pd
import plotly.express as px
import streamlit as st
from dashboard.styles import get_plotly_layout_defaults


def render_demand_page(df: pd.DataFrame):
    """Render Page 1: Executive Overview & Demand Trends (Max 2 charts)."""
    if df.empty:
        st.info("No trip records available for demand analysis.")
        return

    st.markdown("## 📊 Executive Overview & Demand Volume")
    st.markdown("---")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### 🔥 Hourly Trip Demand & Peak Hours")
        if "pickup_hour" in df.columns:
            hourly_df = (
                df.groupby("pickup_hour")
                .agg(
                    trips=("fare_amount", "count"),
                    revenue=("total_amount", "sum"),
                    avg_fare=("fare_amount", "mean"),
                )
                .reset_index()
            )

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
            st.plotly_chart(fig_hour, use_container_width=True)

    with c2:
        st.markdown("### 📅 Day of Week Volume Curve")
        if "pickup_day_of_week" in df.columns:
            dow_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            dow_df = (
                df.groupby("pickup_day_of_week")
                .agg(
                    trips=("fare_amount", "count"),
                    avg_fare=("fare_amount", "mean"),
                    revenue=("total_amount", "sum"),
                )
                .reset_index()
            )
            dow_df["pickup_day_of_week"] = pd.Categorical(
                dow_df["pickup_day_of_week"], categories=dow_order, ordered=True
            )
            dow_df = dow_df.sort_values("pickup_day_of_week")

            fig_dow = px.area(
                dow_df,
                x="pickup_day_of_week",
                y="trips",
                markers=True,
                color_discrete_sequence=["#38BDF8"],
                labels={
                    "pickup_day_of_week": "Day of Week",
                    "trips": "Trip Volume",
                },
                title="Weekly Trip Volume Profile",
            )
            fig_dow.update_layout(**get_plotly_layout_defaults(), height=420)
            st.plotly_chart(fig_dow, use_container_width=True)

    # 3. Monthly Demand & Revenue Trend Profile across 2025 (Full Year Overview)
    if "pickup_month" in df.columns:
        month_map = {
            1: "Jan",
            2: "Feb",
            3: "Mar",
            4: "Apr",
            5: "May",
            6: "Jun",
            7: "Jul",
            8: "Aug",
            9: "Sep",
            10: "Oct",
            11: "Nov",
            12: "Dec",
        }
        monthly_df = (
            df.groupby("pickup_month")
            .agg(
                trips=("fare_amount", "count"),
                revenue=("total_amount", "sum"),
                avg_fare=("fare_amount", "mean"),
            )
            .reset_index()
        )
        monthly_df["month_name"] = monthly_df["pickup_month"].map(month_map)

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
            st.plotly_chart(fig_m_trips, use_container_width=True)

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
            st.plotly_chart(fig_m_rev, use_container_width=True)
