"""KPI Metric Cards Component."""

import pandas as pd
import streamlit as st


def render_kpi_cards(df: pd.DataFrame):
    """Render 6 KPI cards across columns with modern formatting."""
    if df.empty:
        return

    total_trips = len(df)
    total_revenue = df["total_amount"].sum() if "total_amount" in df.columns else 0.0
    avg_fare = df["fare_amount"].mean() if "fare_amount" in df.columns else 0.0
    avg_distance = df["trip_distance"].mean() if "trip_distance" in df.columns else 0.0
    avg_duration = (
        df["trip_duration_minutes"].mean()
        if "trip_duration_minutes" in df.columns
        else 0.0
    )
    avg_tip = df["tip_percentage"].mean() if "tip_percentage" in df.columns else 0.0

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Trips</div>
                <div class="kpi-value">{total_trips:,}</div>
                <span class="kpi-badge badge-amber">🚕 Volume</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Revenue</div>
                <div class="kpi-value">${total_revenue:,.2f}</div>
                <span class="kpi-badge badge-cyan">💰 Gross</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Avg Fare</div>
                <div class="kpi-value">${avg_fare:.2f}</div>
                <span class="kpi-badge badge-emerald">💵 Per Trip</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Avg Distance</div>
                <div class="kpi-value">{avg_distance:.2f} mi</div>
                <span class="kpi-badge badge-purple">📍 Distance</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c5:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Avg Duration</div>
                <div class="kpi-value">{avg_duration:.1f} min</div>
                <span class="kpi-badge badge-rose">⏱️ Time</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c6:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-title">Avg Tip %</div>
                <div class="kpi-value">{avg_tip:.1f}%</div>
                <span class="kpi-badge badge-amber">✨ Tipped</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
