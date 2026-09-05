"""Trip Economics & Payment Analysis Component."""

import pandas as pd
import plotly.express as px
import streamlit as st
from dashboard.styles import get_plotly_layout_defaults


def render_economics_tab(df: pd.DataFrame):
    """Render payment methods, tip propensity, and fare/distance distributions."""
    if df.empty:
        st.info("No data available for trip economics.")
        return

    st.markdown("### 💳 Economics, Tip Propensity & Distributions")

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("💳 Payment Method Split")
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
                title="Trip Volume by Payment Method",
            )
            fig_pay.update_layout(**get_plotly_layout_defaults(), height=380)
            st.plotly_chart(fig_pay, use_container_width=True)

    with c2:
        st.subheader("✨ Tip Propensity & Tipped Trips")
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
                    "Tipped Trips": "#10b981",
                    "Non-Tipped Trips": "#64748b",
                },
                text_auto=True,
                title="Tipped vs Non-Tipped Volume",
            )
            fig_tip.update_layout(**get_plotly_layout_defaults(), height=380)
            st.plotly_chart(fig_tip, use_container_width=True)

    st.markdown("---")

    c3, c4 = st.columns(2)

    with c3:
        st.subheader("💵 Fare Amount Distribution")
        if "fare_amount" in df.columns:
            fare_filtered = df[(df["fare_amount"] >= 0) & (df["fare_amount"] <= 100)]
            fig_fare = px.histogram(
                fare_filtered,
                x="fare_amount",
                nbins=35,
                title="Fare Distribution ($0 - $100)",
                color_discrete_sequence=["#ec4899"],
                labels={"fare_amount": "Fare Amount ($)"},
            )
            fig_fare.update_layout(**get_plotly_layout_defaults(), height=360)
            st.plotly_chart(fig_fare, use_container_width=True)

    with c4:
        st.subheader("📏 Trip Distance Distribution")
        if "trip_distance" in df.columns:
            dist_filtered = df[(df["trip_distance"] > 0) & (df["trip_distance"] <= 30)]
            fig_dist = px.histogram(
                dist_filtered,
                x="trip_distance",
                nbins=35,
                title="Distance Distribution (0 - 30 Miles)",
                color_discrete_sequence=["#8b5cf6"],
                labels={"trip_distance": "Trip Distance (Miles)"},
            )
            fig_dist.update_layout(**get_plotly_layout_defaults(), height=360)
            st.plotly_chart(fig_dist, use_container_width=True)
