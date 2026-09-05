"""Distribution Histograms Component."""

import pandas as pd
import plotly.express as px
import streamlit as st
from dashboard.styles import get_plotly_layout_defaults


def render_distribution_tab(df: pd.DataFrame):
    """Render fare amount and trip distance distribution histograms."""
    if df.empty:
        st.info("No data available for distribution analysis.")
        return

    c1, c2 = st.columns(2)

    with c1:
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
            fig_fare.update_layout(**get_plotly_layout_defaults(), height=380)
            st.plotly_chart(fig_fare, use_container_width=True)

    with c2:
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
            fig_dist.update_layout(**get_plotly_layout_defaults(), height=380)
            st.plotly_chart(fig_dist, use_container_width=True)
