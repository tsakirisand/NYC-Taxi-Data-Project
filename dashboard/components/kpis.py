"""KPI Metric Cards Component with Large-Number Formatting."""

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


def render_kpi_cards(df: pd.DataFrame, totals_dict: Optional[Dict[str, float]] = None):
    """Render 6 KPI cards across a 3x2 responsive grid preventing text truncation."""
    if df.empty:
        return

    if totals_dict and len(df) >= 300000:
        total_trips = int(totals_dict.get("total_trips", len(df)))
        total_revenue = float(
            totals_dict.get("total_revenue", df["total_amount"].sum())
        )
        avg_fare = float(totals_dict.get("avg_fare", df["fare_amount"].mean()))
        avg_distance = float(
            totals_dict.get("avg_distance", df["trip_distance"].mean())
        )
        avg_duration = float(
            totals_dict.get("avg_duration", df["trip_duration_minutes"].mean())
        )
        avg_tip = float(totals_dict.get("avg_tip", df["tip_percentage"].mean()))
    else:
        total_trips = len(df)
        total_revenue = (
            df["total_amount"].sum() if "total_amount" in df.columns else 0.0
        )
        avg_fare = df["fare_amount"].mean() if "fare_amount" in df.columns else 0.0
        avg_distance = (
            df["trip_distance"].mean() if "trip_distance" in df.columns else 0.0
        )
        avg_duration = (
            df["trip_duration_minutes"].mean()
            if "trip_duration_minutes" in df.columns
            else 0.0
        )
        avg_tip = df["tip_percentage"].mean() if "tip_percentage" in df.columns else 0.0

    # Row 1: Total Trips, Total Revenue, Avg Fare
    r1_col1, r1_col2, r1_col3 = st.columns(3)

    with r1_col1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Trips</div>
                <div class="kpi-value">{format_count(total_trips)}</div>
                <span class="kpi-badge badge-amber">🚕 Exact: {total_trips:,} trips</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with r1_col2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Revenue</div>
                <div class="kpi-value">{format_currency(total_revenue)}</div>
                <span class="kpi-badge badge-cyan">💰 Gross: ${total_revenue:,.2f}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with r1_col3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Average Fare</div>
                <div class="kpi-value">${avg_fare:.2f}</div>
                <span class="kpi-badge badge-emerald">💵 Per Trip Average</span>
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
            <div class="kpi-card">
                <div class="kpi-title">Average Trip Distance</div>
                <div class="kpi-value">{avg_distance:.2f} miles</div>
                <span class="kpi-badge badge-purple">📍 Distance Metric</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with r2_col2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Average Trip Duration</div>
                <div class="kpi-value">{avg_duration:.1f} minutes</div>
                <span class="kpi-badge badge-rose">⏱️ Duration Metric</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with r2_col3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Average Tip Percentage</div>
                <div class="kpi-value">{avg_tip:.1f}%</div>
                <span class="kpi-badge badge-amber">✨ Tipped Percentage</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
