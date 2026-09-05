"""Temporal, Speed & Duration Insights Component."""

import pandas as pd
import plotly.express as px
import streamlit as st
from dashboard.styles import get_plotly_layout_defaults


def render_temporal_tab(df: pd.DataFrame):
    """Render rush hour, speed profile, and duration analysis."""
    if df.empty:
        st.info("No data available for temporal analysis.")
        return

    st.markdown("### ⏱️ Temporal, Speed & Duration Insights")

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("⚡ Average Speed Profile by Hour of Day")
        if "pickup_hour" in df.columns and "avg_speed_mph" in df.columns:
            speed_df = df.groupby("pickup_hour")["avg_speed_mph"].mean().reset_index()
            fig_speed = px.line(
                speed_df,
                x="pickup_hour",
                y="avg_speed_mph",
                markers=True,
                line_shape="spline",
                color_discrete_sequence=["#06b6d4"],
                labels={
                    "pickup_hour": "Hour of Day (0-23)",
                    "avg_speed_mph": "Average Speed (mph)",
                },
                title="City Velocity Profile Across 24 Hours",
            )
            fig_speed.update_layout(**get_plotly_layout_defaults(), height=380)
            st.plotly_chart(fig_speed, use_container_width=True)

    with c2:
        st.subheader("🏙️ Rush Hour vs Off-Peak Performance")
        if "is_peak_hour" in df.columns:
            peak_map = {True: "Peak Rush Hour", False: "Off-Peak"}
            peak_df = df.copy()
            peak_df["Peak Category"] = peak_df["is_peak_hour"].map(peak_map)

            peak_summary = (
                peak_df.groupby("Peak Category")
                .agg(
                    total_trips=("fare_amount", "count"),
                    avg_speed=("avg_speed_mph", "mean"),
                    avg_duration=("trip_duration_minutes", "mean"),
                    avg_fare=("fare_amount", "mean"),
                )
                .reset_index()
            )

            fig_peak = px.bar(
                peak_summary,
                x="Peak Category",
                y="avg_duration",
                color="Peak Category",
                color_discrete_map={
                    "Peak Rush Hour": "#ec4899",
                    "Off-Peak": "#f59e0b",
                },
                text_auto=".1f",
                title="Average Trip Duration: Peak vs Off-Peak (Mins)",
            )
            fig_peak.update_layout(**get_plotly_layout_defaults(), height=380)
            st.plotly_chart(fig_peak, use_container_width=True)
