"""Spatial & Payment Analysis Component."""

import pandas as pd
import plotly.express as px
import streamlit as st
from dashboard.styles import get_plotly_layout_defaults


def render_spatial_tab(df: pd.DataFrame):
    """Render spatial pickup zones and payment method breakdown tab."""
    if df.empty:
        st.info("No spatial data available.")
        return

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("📍 Top Busiest Pickup Taxi Zones")
        if "pickup_zone_name" in df.columns:
            top_zones = (
                df.groupby("pickup_zone_name")
                .size()
                .reset_index(name="trip_count")
                .sort_values("trip_count", ascending=False)
                .head(10)
            )

            fig_zones = px.bar(
                top_zones,
                x="trip_count",
                y="pickup_zone_name",
                orientation="h",
                color="trip_count",
                color_continuous_scale="Viridis",
                labels={
                    "trip_count": "Total Pickups",
                    "pickup_zone_name": "Taxi Zone",
                },
                title="Top 10 Pickup Zones",
            )
            fig_zones.update_layout(
                **get_plotly_layout_defaults(),
                height=400,
            )
            fig_zones.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_zones, use_container_width=True)

    with c2:
        st.subheader("💳 Payment Method Distribution")
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
                    "#06b6d4",
                    "#f59e0b",
                    "#ec4899",
                    "#8b5cf6",
                ],
                title="Payment Type Split",
            )
            fig_pay.update_layout(**get_plotly_layout_defaults(), height=400)
            st.plotly_chart(fig_pay, use_container_width=True)
