"""Trip Economics, Speed Profile & SQL Workbench Component (Page 3)."""

from typing import Dict, Any, Optional
import pandas as pd
import plotly.express as px
import streamlit as st
from dashboard.components.analytics_view import render_analytics_tab
from dashboard.data_service import (
    make_filter_key,
    query_payment_breakdown,
    query_tipping_summary,
    query_speed_by_hour,
    query_rush_hour_summary,
)
from dashboard.styles import get_plotly_layout_defaults


def render_economics_page(
    df: Optional[pd.DataFrame] = None, filter_spec: Optional[Dict[str, Any]] = None
):
    """Render Page 3: Economics, Speed Velocity Profile & SQL Workbench with 100% full-dataset aggregations."""
    filter_key = make_filter_key(filter_spec)

    st.markdown("## 💳 Economics, Speed Velocity & SQL Workbench")
    st.markdown("---")

    # --- Section 1: Payment Split & Tip Propensity ---
    st.markdown("### 💳 Section 1: Payment Split & Tipping Behavior")
    c1, c2 = st.columns(2)

    with c1:
        pay_df = query_payment_breakdown(filter_key, filter_spec)
        if not pay_df.empty:
            fig_pay = px.pie(
                pay_df,
                names="payment_label",
                values="trips",
                hole=0.45,
                color_discrete_sequence=[
                    "#005BAE",
                    "#0284C7",
                    "#38BDF8",
                    "#F59E0B",
                    "#64748B",
                ],
                title="Payment Method Breakdown",
            )
            fig_pay.update_layout(
                **get_plotly_layout_defaults(),
                height=380,
                legend=dict(
                    orientation="v",
                    y=0.5,
                    x=1.02,
                    xanchor="left",
                    yanchor="middle",
                ),
            )
            st.plotly_chart(fig_pay, use_container_width=True)

    with c2:
        tip_summary = query_tipping_summary(filter_key, filter_spec)
        if not tip_summary.empty:
            fig_tip = px.bar(
                tip_summary,
                x="Category",
                y="Count",
                color="Category",
                color_discrete_map={
                    "Tipped Trips": "#10B981",
                    "Non-Tipped Trips": "#64748B",
                },
                text_auto=True,
                title="Tipped vs Non-Tipped Volume",
            )
            fig_tip.update_layout(**get_plotly_layout_defaults(), height=380)
            st.plotly_chart(fig_tip, use_container_width=True)

    st.markdown("---")

    # --- Section 2: City Speed Velocity Profile ---
    st.markdown("### ⏱️ Section 2: City Velocity & Rush Hour Performance")
    c3, c4 = st.columns(2)

    with c3:
        speed_df = query_speed_by_hour(filter_key, filter_spec)
        if not speed_df.empty:
            fig_speed = px.line(
                speed_df,
                x="pickup_hour",
                y="avg_speed_mph",
                markers=True,
                line_shape="spline",
                color_discrete_sequence=["#38BDF8"],
                labels={
                    "pickup_hour": "Hour of Day (0-23)",
                    "avg_speed_mph": "Average Speed (mph)",
                },
                title="City Velocity Profile Across 24 Hours",
            )
            fig_speed.update_layout(**get_plotly_layout_defaults(), height=380)
            st.plotly_chart(fig_speed, use_container_width=True)

    with c4:
        peak_summary = query_rush_hour_summary(filter_key, filter_spec)
        if not peak_summary.empty:
            peak_summary.rename(
                columns={"peak_category": "Peak Category"}, inplace=True
            )
            fig_peak = px.bar(
                peak_summary,
                x="Peak Category",
                y="avg_duration",
                color="Peak Category",
                color_discrete_map={
                    "Peak Rush Hour": "#005BAE",
                    "Off-Peak": "#64748B",
                },
                text_auto=".1f",
                labels={"avg_duration": "Avg Duration (Minutes)"},
                title="Trip Duration: Peak vs Off-Peak",
            )
            fig_peak.update_layout(**get_plotly_layout_defaults(), height=380)
            st.plotly_chart(fig_peak, use_container_width=True)

    st.markdown("---")

    # --- Section 3: Interactive SQL Workbench ---
    st.markdown("### 💻 Section 3: Interactive SQL Workbench & Data Explorer")
    render_analytics_tab(df)
