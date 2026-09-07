"""NYC Yellow Taxi Data Engineering - Interactive Analytics Portal.

Modular Multi-Page Streamlit Dashboard with 4 focused pages:
1. Executive Overview & Demand Trends
2. Spatial & Taxi Zone Performance
3. Trip Economics, Speed Velocity & SQL Workbench
4. Executive Report & Insights
"""

import sys
from pathlib import Path

# Ensure root package path resolution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from dashboard.components.demand_charts import render_demand_page  # noqa: E402
from dashboard.components.economics_charts import render_economics_page  # noqa: E402
from dashboard.components.kpis import render_kpi_cards  # noqa: E402
from dashboard.components.reports_view import render_reports_page  # noqa: E402
from dashboard.components.sidebar import render_sidebar_filters  # noqa: E402
from dashboard.components.spatial_charts import render_spatial_page  # noqa: E402
from dashboard.styles import inject_custom_css  # noqa: E402
from src.database.load_postgres import DatabaseLoader  # noqa: E402
from src.utils.config import settings  # noqa: E402

# 1. Page Configuration
st.set_page_config(
    page_title="NYC Yellow Taxi Analytics",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Inject Custom Theme & Design System
inject_custom_css()


@st.cache_data(ttl=600)
def load_dashboard_data():
    """Load optimized multi-month fact trips sample for tabular explorer and zone lookup."""
    val_files = sorted(settings.VALIDATED_DATA_DIR.glob("*.parquet"))
    zone_path = settings.REFERENCE_DATA_DIR / "taxi_zone_lookup.csv"

    # Taxi Zone Lookup Table
    if zone_path.exists():
        zones_df = pd.read_csv(zone_path)
        z_id = "LocationID" if "LocationID" in zones_df.columns else "location_id"
        z_name = "Zone" if "Zone" in zones_df.columns else "pickup_zone_name"
        zone_dict = dict(zip(zones_df[z_id], zones_df[z_name]))
    else:
        zones_df = pd.DataFrame()
        zone_dict = {}

    try:
        import duckdb

        con = duckdb.connect()
        # Representative Multi-Month Stratified Sample for Interactive Data Previews (25k rows/month)
        trips_df = con.query("""
            WITH sampled AS (
                SELECT *,
                    month(tpep_pickup_datetime) as pickup_month,
                    hour(tpep_pickup_datetime) as pickup_hour,
                    strftime(tpep_pickup_datetime, '%a') as pickup_day_of_week,
                    epoch(tpep_dropoff_datetime - tpep_pickup_datetime)/60.0 as trip_duration_minutes,
                    CASE WHEN epoch(tpep_dropoff_datetime - tpep_pickup_datetime) > 0 
                         THEN trip_distance / (epoch(tpep_dropoff_datetime - tpep_pickup_datetime)/3600.0)
                         ELSE 0.0 END as avg_speed_mph,
                    CASE WHEN fare_amount > 0 THEN (tip_amount / fare_amount) * 100.0 ELSE 0.0 END as tip_percentage,
                    CASE WHEN dayofweek(tpep_pickup_datetime) BETWEEN 1 AND 5 
                         AND (hour(tpep_pickup_datetime) BETWEEN 7 AND 9 OR hour(tpep_pickup_datetime) BETWEEN 16 AND 19)
                         THEN true ELSE false END as is_peak_hour,
                    row_number() OVER (PARTITION BY month(tpep_pickup_datetime)) as rn
                FROM 'data/validated/*.parquet'
            )
            SELECT 
                fare_amount, total_amount, trip_distance, tip_amount,
                PULocationID as pulocation_id, payment_type,
                trip_duration_minutes, avg_speed_mph, tip_percentage,
                pickup_month, pickup_hour, pickup_day_of_week, is_peak_hour
            FROM sampled
            WHERE rn <= 25000
            """).df()

        trips_df["pickup_zone_name"] = trips_df["pulocation_id"].map(zone_dict)

    except Exception:
        # Fallback to Database / Parquet reading if DuckDB query fails
        loader = DatabaseLoader()
        engine = loader.engine

        try:
            trips_df = pd.read_sql(
                """
                SELECT
                    fare_amount, total_amount, trip_distance, tip_amount,
                    pulocation_id, payment_type,
                    trip_duration_minutes, avg_speed_mph, tip_percentage,
                    CAST(strftime('%m', tpep_pickup_datetime) AS INTEGER) as pickup_month,
                    CAST(strftime('%H', tpep_pickup_datetime) AS INTEGER) as pickup_hour,
                    strftime('%a', tpep_pickup_datetime) as pickup_day_of_week,
                    is_peak_hour
                FROM fact_trips
                WHERE (rowid % 140) = 0
                """,
                con=engine,
            )
            trips_df["pickup_zone_name"] = trips_df["pulocation_id"].map(zone_dict)

        except Exception:
            if val_files:
                trips_df = pd.concat(
                    [pd.read_parquet(f) for f in val_files], ignore_index=True
                )
            else:
                trips_df = pd.DataFrame()

            pu_col = (
                "pulocation_id"
                if "pulocation_id" in trips_df.columns
                else "PULocationID" if "PULocationID" in trips_df.columns else None
            )
            if not trips_df.empty and pu_col and not zones_df.empty:
                trips_df["pickup_zone_name"] = trips_df[pu_col].map(zone_dict)

    # Clean human-readable transformations
    if not trips_df.empty:
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
        if "is_peak_hour" in trips_df.columns:
            trips_df["rush_hour_status"] = (
                trips_df["is_peak_hour"].map(peak_map).fillna("Off-Peak")
            )
    return trips_df, zones_df


def main():
    # 1. Sidebar Navigation Menu Styled as Pill Tabs
    selected_page = st.sidebar.radio(
        "Select Page",
        options=[
            "📊 Executive Overview",
            "📍 Spatial & Zone Analytics",
            "💳 Economics & SQL Workbench",
            "💡 Executive Report & Insights",
        ],
        label_visibility="collapsed",
    )
    st.sidebar.markdown("---")

    trips_df, zones_df = load_dashboard_data()

    if trips_df.empty:
        st.warning(
            "⚠️ No dataset found or database cache refreshing. Please click below to reload."
        )
        if st.button("🔄 Reload Dashboard Data"):
            st.cache_data.clear()
            st.rerun()
        st.stop()

    # 2. Render Sidebar Filters & Return Filtered Dataset + Filter Spec
    filtered_df, filter_spec = render_sidebar_filters(trips_df, zones_df)

    # 3. Main Content Views based on Selected Sidebar Navigation Pill Tab
    if "Executive Overview" in selected_page:
        st.markdown(
            """
            <div class="main-header">
                <h1 class="main-header-title">🚕 NYC Yellow Taxi Executive Dashboard</h1>
                <p class="main-header-subtitle">
                    Enterprise End-to-End Data Pipeline • PySpark Distributed Compute • PostgreSQL Data Warehouse
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # 4x2 KPI Cards (100% full dataset exact SQL aggregations)
        render_kpi_cards(filtered_df, filter_spec=filter_spec)
        st.markdown("<br>", unsafe_allow_html=True)
        # Visual Demand Trends & Volume Profiles
        render_demand_page(filtered_df, filter_spec=filter_spec)

    elif "Spatial" in selected_page:
        st.markdown(
            """
            <div class="main-header">
                <h1 class="main-header-title">📍 Spatial & Taxi Zone Performance</h1>
                <p class="main-header-subtitle">
                    Pickup Zone Rankings • Geographic Demand Distribution • Revenue Hotspots
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_spatial_page(filtered_df, filter_spec=filter_spec)

    elif "Economics" in selected_page:
        st.markdown(
            """
            <div class="main-header">
                <h1 class="main-header-title">💳 Economics, Speed & SQL Workbench</h1>
                <p class="main-header-subtitle">
                    Payment Method Split • Tipping Behavior • Velocity Profiles • Interactive SQL Editor
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_economics_page(filtered_df, filter_spec=filter_spec)

    elif "Report" in selected_page:
        st.markdown(
            """
            <div class="main-header">
                <h1 class="main-header-title">💡 Executive Report & Urban Analytics Insights</h1>
                <p class="main-header-subtitle">
                    Comprehensive Empirical Data Analysis • Policy Recommendations • Downloadable Artifacts
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_reports_page(filtered_df, filter_spec=filter_spec)


if __name__ == "__main__":
    main()
