"""KPI Metric Cards Component matching Greek Tourism Analytics UI standard."""

from typing import Dict, Any, Optional
import pandas as pd
import streamlit as st
from dashboard.data_service import query_kpis, make_filter_key


def format_currency(val: float) -> str:
    """Format large currency values cleanly."""
    if val >= 1_000_000_000:
        return f"${val / 1_000_000_000:.2f}B"
    elif val >= 1_000_000:
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
    df: Optional[pd.DataFrame] = None,
    totals_dict: Optional[Dict[str, float]] = None,
    sample_ratio: float = 1.0,
    filter_spec: Optional[Dict[str, Any]] = None,
    **kwargs,
):
    """Render 8 clean metric cards across a 4x2 grid with 100% exact full dataset aggregations."""
    filter_key = make_filter_key(filter_spec)
    kpis = query_kpis(filter_key, filter_spec)

    total_trips = int(kpis["total_trips"])
    total_revenue = float(kpis["total_revenue"])
    total_tips = float(kpis["total_tips"])
    avg_fare = float(kpis["avg_fare"])
    avg_distance = float(kpis["avg_distance"])
    avg_duration = float(kpis["avg_duration"])
    avg_speed = float(kpis["avg_speed"])
    avg_tip = float(kpis["avg_tip_pct"])

    # Row 1: Total Trips, Total Revenue, Total Tips, Average Fare
    r1_col1, r1_col2, r1_col3, r1_col4 = st.columns(4)

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
            <div class="metric-card" style="border-left-color: #059669;">
                <div class="metric-label">Total Tips</div>
                <div class="metric-value" style="color: #10B981;">{format_currency(total_tips)}</div>
                <div class="metric-badge">💵 Tips: ${total_tips:,.2f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with r1_col4:
        st.markdown(
            f"""
            <div class="metric-card" style="border-left-color: #10B981;">
                <div class="metric-label">Average Fare</div>
                <div class="metric-value" style="color: #34D399;">${avg_fare:.2f}</div>
                <div class="metric-badge">💳 Per Trip Fare</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-bottom: 0.8rem;'></div>", unsafe_allow_html=True)

    # Row 2: Avg Distance, Avg Duration, Avg Speed, Avg Tip %
    r2_col1, r2_col2, r2_col3, r2_col4 = st.columns(4)

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
            <div class="metric-card" style="border-left-color: #38BDF8;">
                <div class="metric-label">Average Speed</div>
                <div class="metric-value" style="color: #38BDF8;">{avg_speed:.1f} mph</div>
                <div class="metric-badge">⚡ City Velocity</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with r2_col4:
        st.markdown(
            f"""
            <div class="metric-card" style="border-left-color: #EC4899;">
                <div class="metric-label">Average Tip %</div>
                <div class="metric-value" style="color: #F472B6;">{avg_tip:.1f}%</div>
                <div class="metric-badge">✨ Tip Ratio</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
