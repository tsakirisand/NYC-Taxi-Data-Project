"""KPI Metric Cards Component matching Greek Tourism Analytics UI standard."""

from typing import Dict, Optional
import pandas as pd
import streamlit as st


def format_currency(val: float) -> str:
    """Format large currency values cleanly."""
    if val >= 1_000_000:
        return f"${val / 1_000_000:.2f}M"
    elif val >= 1_000:
        return f"${val / 1_000:.1f}K"
    return f"${val:.2f}"


def format_count(val: float) -> str:
    """Format large counts cleanly."""
    if val >= 1_000_000:
        return f"{val / 1_000_000:.2f}M"
    elif val >= 1_000:
        return f"{val / 1_000:.1f}K"
    return f"{int(val):,}"


def render_kpi_cards(
    df: pd.DataFrame,
    totals_dict: Optional[Dict[str, float]] = None,
    sample_ratio: float = 1.0,
):
    """Render 6 clean metric cards across a 3x2 grid matching Greek Tourism UI style."""
    if df.empty:
        return

    # Check if unfiltered dataset is being rendered
    is_unfiltered = (
        totals_dict
        and "total_trips" in totals_dict
        and totals_dict["total_trips"] > 0
        and (
            "unfiltered_len" not in totals_dict
            or len(df) >= totals_dict.get("unfiltered_len", len(df))
        )
    )

    if is_unfiltered:
        total_trips = int(totals_dict["total_trips"])
        total_revenue = float(totals_dict["total_revenue"])
        avg_fare = float(totals_dict.get("avg_fare", df["fare_amount"].mean()))
        avg_distance = float(
            totals_dict.get("avg_distance", df["trip_distance"].mean())
        )
        avg_duration = float(
            totals_dict.get("avg_duration", df["trip_duration_minutes"].mean())
        )
        avg_tip = float(totals_dict.get("avg_tip", df["tip_percentage"].mean()))
    else:
        scale = max(sample_ratio, 1.0)
        total_trips = int(len(df) * scale)
        total_revenue = (
            float(df["total_amount"].sum() * scale)
            if "total_amount" in df.columns
            else 0.0
        )
        avg_fare = (
            float(df["fare_amount"].mean())
            if "fare_amount" in df.columns and not df.empty
            else 0.0
        )
        avg_distance = (
            float(df["trip_distance"].mean())
            if "trip_distance" in df.columns and not df.empty
            else 0.0
        )
        avg_duration = (
            float(df["trip_duration_minutes"].mean())
            if "trip_duration_minutes" in df.columns and not df.empty
            else 0.0
        )
        avg_tip = (
            float(df["tip_percentage"].mean())
            if "tip_percentage" in df.columns and not df.empty
            else 0.0
        )

    # Row 1: Total Trips, Total Revenue, Avg Fare
    r1_col1, r1_col2, r1_col3 = st.columns(3)

    with r1_col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">Total Trips</div>
                <div class="metric-value">{format_count(total_trips)}</div>
                <div class="metric-badge">🚕 Exact: {total_trips:,} trips</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with r1_col2:
        st.markdown(
            f"""
            <div class="metric-card" style="border-left-color: #0284C7;">
                <div class="metric-label">Total Revenue</div>
                <div class="metric-value" style="color: #0284C7;">{format_currency(total_revenue)}</div>
                <div class="metric-badge">💰 Gross: ${total_revenue:,.2f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with r1_col3:
        st.markdown(
            f"""
            <div class="metric-card" style="border-left-color: #10B981;">
                <div class="metric-label">Average Fare</div>
                <div class="metric-value" style="color: #10B981;">${avg_fare:.2f}</div>
                <div class="metric-badge">💵 Per Trip Average</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom: 0.8rem;'></div>", unsafe_allow_html=True)

    # Row 2: Avg Distance, Avg Duration, Avg Tip %
    r2_col1, r2_col2, r2_col3 = st.columns(3)

    with r2_col1:
        st.markdown(
            f"""
            <div class="metric-card" style="border-left-color: #8B5CF6;">
                <div class="metric-label">Average Distance</div>
                <div class="metric-value" style="color: #A78BFA;">{avg_distance:.2f} mi</div>
                <div class="metric-badge">📍 Trip Distance</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with r2_col2:
        st.markdown(
            f"""
            <div class="metric-card" style="border-left-color: #F59E0B;">
                <div class="metric-label">Average Duration</div>
                <div class="metric-value" style="color: #FBBF24;">{avg_duration:.1f} min</div>
                <div class="metric-badge">⏱️ Trip Time</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with r2_col3:
        st.markdown(
            f"""
            <div class="metric-card" style="border-left-color: #EC4899;">
                <div class="metric-label">Average Tip %</div>
                <div class="metric-value" style="color: #F472B6;">{avg_tip:.1f}%</div>
                <div class="metric-badge">✨ Tipped Ratio</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
