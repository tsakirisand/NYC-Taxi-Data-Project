"""Trip Economics, Speed Profile & SQL Workbench Component (Page 3)."""

import pandas as pd
import plotly.express as px
import streamlit as st
from dashboard.components.analytics_view import render_analytics_tab
from dashboard.styles import get_plotly_layout_defaults


def render_economics_page(df: pd.DataFrame):
    """Render Page 3: Economics, Speed Velocity Profile & SQL Workbench."""
    if df.empty:
        st.info("No data available for trip economics.")
        return

    st.markdown("## 💳 Economics, Speed Velocity & SQL Workbench")
    st.markdown("---")

    # --- Section 1: Payment Split & Tip Propensity ---
    st.markdown("### 💳 Section 1: Payment Split & Tipping Behavior")
    c1, c2 = st.columns(2)

    with c1:
        if "payment_type" in df.columns:
            payment_map = {
                1: "Credit Card",
                2: "Cash",
                3: "No Charge",
                4: "Dispute",
            }
            pay_df = df["payment_type"].map(payment_map).value_counts().reset_index()
            pay_df.columns = ["Payment Method", "Count"]

            fig_pay = px.pie(
                pay_df,
                names="Payment Method",
                values="Count",
                hole=0.45,
                color_discrete_sequence=[
                    "#005BAE",
                    "#0284C7",
                    "#38BDF8",
                    "#F59E0B",
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
        if "tip_amount" in df.columns:
            tipped_count = (df["tip_amount"] > 0).sum()
            untipped_count = len(df) - tipped_count
            tip_summary = pd.DataFrame(
                {
                    "Category": ["Tipped Trips", "Non-Tipped Trips"],
                    "Count": [tipped_count, untipped_count],
                }
            )

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
        if "pickup_hour" in df.columns and "avg_speed_mph" in df.columns:
            speed_df = df.groupby("pickup_hour")["avg_speed_mph"].mean().reset_index()
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
        peak_df = df.copy()
        if "rush_hour_status" not in peak_df.columns:
            peak_map = {
                True: "Peak Rush Hour",
                False: "Off-Peak",
                1: "Peak Rush Hour",
                0: "Off-Peak",
                "1": "Peak Rush Hour",
                "0": "Off-Peak",
                "True": "Peak Rush Hour",
                "False": "Off-Peak",
            }
            if "is_peak_hour" in peak_df.columns:
                peak_df["rush_hour_status"] = (
                    peak_df["is_peak_hour"].map(peak_map).fillna("Off-Peak")
                )
            else:
                peak_df["rush_hour_status"] = "Off-Peak"

        peak_summary = (
            peak_df.groupby("rush_hour_status")
            .agg(
                avg_duration=("trip_duration_minutes", "mean"),
                avg_speed=("avg_speed_mph", "mean"),
            )
            .reset_index()
        )
        peak_summary.rename(columns={"rush_hour_status": "Peak Category"}, inplace=True)

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
