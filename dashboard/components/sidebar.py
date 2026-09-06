"""Sidebar Filter Controls Component."""

import pandas as pd
import streamlit as st


def render_sidebar_filters(
    trips_df: pd.DataFrame, zones_df: pd.DataFrame
) -> pd.DataFrame:
    """Render clean interactive sidebar filter panel."""
    st.sidebar.markdown("### 🔍 Global Filters")

    if trips_df.empty:
        return trips_df

    # 1. Month Filter
    available_months = (
        sorted(trips_df["pickup_month"].unique())
        if "pickup_month" in trips_df.columns
        else [1]
    )
    month_names = {
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

    selected_months = st.sidebar.multiselect(
        "Select Months (2025)",
        options=available_months,
        format_func=lambda x: f"{month_names.get(x, x)} (Month {x})",
        default=available_months,
    )

    # 2. Pickup Zone Filter
    if "pickup_zone_name" in trips_df.columns:
        zone_options = sorted(trips_df["pickup_zone_name"].dropna().unique())
        selected_zones = st.sidebar.multiselect(
            "Filter Pickup Zones", options=zone_options, default=[]
        )
    else:
        selected_zones = []

    # 3. Payment Method Filter
    payment_map = {1: "Credit Card", 2: "Cash", 3: "No Charge", 4: "Dispute"}
    selected_payments = st.sidebar.multiselect(
        "Payment Methods",
        options=list(payment_map.keys()),
        format_func=lambda x: payment_map.get(x, f"Type {x}"),
        default=list(payment_map.keys()),
    )

    # 4. Distance & Fare Range Sliders
    max_dist_val = (
        float(trips_df["trip_distance"].max())
        if "trip_distance" in trips_df.columns
        else 50.0
    )
    distance_range = st.sidebar.slider(
        "Trip Distance (Miles)",
        min_value=0.0,
        max_value=min(max_dist_val, 100.0),
        value=(0.0, min(max_dist_val, 100.0)),
        step=1.0,
    )

    max_fare_val = (
        float(trips_df["fare_amount"].max())
        if "fare_amount" in trips_df.columns
        else 200.0
    )
    fare_range = st.sidebar.slider(
        "Fare Amount ($)",
        min_value=0.0,
        max_value=min(max_fare_val, 300.0),
        value=(0.0, min(max_fare_val, 300.0)),
        step=5.0,
    )

    # Apply Filtering Logic
    filtered_df = trips_df.copy()

    if selected_months and "pickup_month" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["pickup_month"].isin(selected_months)]

    if selected_zones and "pickup_zone_name" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["pickup_zone_name"].isin(selected_zones)]

    if selected_payments and "payment_type" in filtered_df.columns:
        filtered_df = filtered_df[filtered_df["payment_type"].isin(selected_payments)]

    if "trip_distance" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["trip_distance"] >= distance_range[0])
            & (filtered_df["trip_distance"] <= distance_range[1])
        ]

    if "fare_amount" in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df["fare_amount"] >= fare_range[0])
            & (filtered_df["fare_amount"] <= fare_range[1])
        ]

    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"📊 **Active Volume**: {len(filtered_df):,} trips "
        f"({(len(filtered_df) / max(len(trips_df), 1)) * 100:.1f}% of total)"
    )

    return filtered_df
