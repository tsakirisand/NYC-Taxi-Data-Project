"""Spatial & Taxi Zone Analytics Component (Page 2)."""

from typing import Dict, Any, Optional
import pandas as pd
import plotly.express as px
import streamlit as st
from dashboard.data_service import make_filter_key, query_top_zones
from dashboard.styles import get_plotly_layout_defaults


def render_spatial_page(
    df: Optional[pd.DataFrame] = None,
    filter_spec: Optional[Dict[str, Any]] = None,
    **kwargs,
):
    """Render Page 2: Spatial & Taxi Zone Performance with 100% full-dataset aggregations."""
    filter_key = make_filter_key(filter_spec)

    st.markdown("## 📍 Spatial & Taxi Zone Analytics")
    st.markdown("---")

    c1, c2 = st.columns(2)

    top_zones = query_top_zones(filter_key, filter_spec, limit=10)

    with c1:
        st.markdown("### 📍 Top Busiest Pickup Taxi Zones")
        if not top_zones.empty:
            fig_zones = px.bar(
                top_zones,
                x="trip_count",
                y="pickup_zone_name",
                orientation="h",
                color="trip_count",
                color_continuous_scale=["#0284C7", "#005BAE", "#38BDF8"],
                labels={
                    "trip_count": "Total Pickups",
                    "pickup_zone_name": "Taxi Zone",
                },
                title="Top 10 Pickup Locations",
            )
            fig_zones.update_layout(**get_plotly_layout_defaults(), height=420)
            fig_zones.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_zones, use_container_width=True, config={'displayModeBar': False, 'responsive': True})

    with c2:
        st.markdown("### 🚖 Most Profitable Taxi Zones")
        if not top_zones.empty:
            revenue_zones = top_zones.sort_values(
                "total_revenue", ascending=False
            ).head(10)

            fig_rev = px.bar(
                revenue_zones,
                x="total_revenue",
                y="pickup_zone_name",
                orientation="h",
                color="avg_fare",
                color_continuous_scale=["#059669", "#10B981", "#34D399"],
                labels={
                    "total_revenue": "Total Revenue ($)",
                    "pickup_zone_name": "Taxi Zone",
                    "avg_fare": "Avg Fare ($)",
                },
                title="Top 10 Grossing Taxi Zones",
            )
            fig_rev.update_layout(**get_plotly_layout_defaults(), height=420)
            fig_rev.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_rev, use_container_width=True, config={'displayModeBar': False, 'responsive': True})
