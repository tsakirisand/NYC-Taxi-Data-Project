"""Demand & Hourly Trends Component."""

import pandas as pd
import plotly.express as px
import streamlit as st
from dashboard.styles import get_plotly_layout_defaults


def render_demand_tab(df: pd.DataFrame):
    """Render demand and time-series charts tab."""
    if df.empty:
        st.info("No trip records available for demand analysis.")
        return

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("🔥 Hourly Demand & Peak Rush Hours")
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
                color_continuous_scale="Plasma",
                labels={
                    "pickup_hour": "Hour of Day (0 - 23)",
                    "trips": "Total Trips",
                    "revenue": "Total Revenue ($)",
                },
                title="Hourly Demand Profile",
            )
            fig_hour.update_layout(**get_plotly_layout_defaults(), height=380)
            st.plotly_chart(fig_hour, use_container_width=True)

    with c2:
        st.subheader("📅 Demand Volume by Day of Week")
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
                color_discrete_sequence=["#f59e0b"],
                labels={
                    "pickup_day_of_week": "Day of Week",
                    "trips": "Trip Volume",
                },
                title="Day of Week Demand Curve",
            )
            fig_dow.update_layout(**get_plotly_layout_defaults(), height=380)
            st.plotly_chart(fig_dow, use_container_width=True)
