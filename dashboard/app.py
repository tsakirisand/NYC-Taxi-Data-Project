"""NYC Yellow Taxi Data Engineering - Interactive Analytics Portal.

Modular Multi-Page Streamlit Dashboard with 3 focused pages:
1. Executive Overview & Demand Trends
2. Spatial & Taxi Zone Performance
3. Trip Economics, Speed Velocity & SQL Workbench
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
    """Load optimized fact trips sample and exact totals for fast rendering."""
    loader = DatabaseLoader()
    engine = loader.engine

    try:
        # 1. Instant Exact Dataset Totals
        kpi_df = pd.read_sql(
            """
            SELECT
                COUNT(*) as total_trips,
                SUM(total_amount) as total_revenue,
                AVG(fare_amount) as avg_fare,
                AVG(trip_distance) as avg_distance,
                AVG(trip_duration_minutes) as avg_duration,
                AVG(tip_percentage) as avg_tip
            FROM fact_trips
            """,
            con=engine,
        )
        totals_dict = kpi_df.iloc[0].to_dict()

        # 2. Taxi Zone Lookup Table
        zones_df = pd.read_sql(
            "SELECT location_id, zone as pickup_zone_name, borough as pickup_borough FROM dim_taxi_zone",
            con=engine,
        )
        zone_dict = dict(zip(zones_df["location_id"], zones_df["pickup_zone_name"]))

        # 3. Fast Column-Pruned Sample for Interactive Charts (300k rows)
        trips_df = pd.read_sql(
            """
            SELECT
                fare_amount, total_amount, trip_distance,
                pulocation_id, payment_type,
                trip_duration_minutes, avg_speed_mph, tip_percentage,
                pickup_month, pickup_hour, pickup_day_of_week, is_peak_hour
            FROM fact_trips
            LIMIT 300000
            """,
            con=engine,
        )
        trips_df["pickup_zone_name"] = trips_df["pulocation_id"].map(zone_dict)

    except Exception:
        # Fallback to local Parquet files if DB not populated
        fact_path = settings.PROCESSED_DATA_DIR / "fact_trips.parquet"
        val_path = settings.VALIDATED_DATA_DIR / "yellow_tripdata_2025-01.parquet"
        zone_path = settings.REFERENCE_DATA_DIR / "taxi_zone_lookup.csv"

        if fact_path.exists():
            trips_df = pd.read_parquet(fact_path)
        elif val_path.exists():
            trips_df = pd.read_parquet(val_path)
        else:
            trips_df = pd.DataFrame()

        if zone_path.exists():
            zones_df = pd.read_csv(zone_path)
        else:
            zones_df = pd.DataFrame()

        if (
            not trips_df.empty
            and "PULocationID" in trips_df.columns
            and not zones_df.empty
        ):
            zone_dict = dict(zip(zones_df["LocationID"], zones_df["Zone"]))
            trips_df["pickup_zone_name"] = trips_df["PULocationID"].map(zone_dict)

        totals_dict = {
            "total_trips": len(trips_df),
            "total_revenue": (
                trips_df["total_amount"].sum()
                if "total_amount" in trips_df.columns
                else 0.0
            ),
            "avg_fare": (
                trips_df["fare_amount"].mean()
                if "fare_amount" in trips_df.columns
                else 0.0
            ),
            "avg_distance": (
                trips_df["trip_distance"].mean()
                if "trip_distance" in trips_df.columns
                else 0.0
            ),
            "avg_duration": (
                trips_df["trip_duration_minutes"].mean()
                if "trip_duration_minutes" in trips_df.columns
                else 0.0
            ),
            "avg_tip": (
                trips_df["tip_percentage"].mean()
                if "tip_percentage" in trips_df.columns
                else 0.0
            ),
        }

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

    return trips_df, zones_df, totals_dict


def main():
    # Page Navigation Selector in Sidebar
    st.sidebar.markdown("## 📌 Navigation Menu")
    selected_page = st.sidebar.radio(
        "Select Dashboard Page",
        options=[
            "📊 Executive Overview",
            "📍 Spatial & Zone Analytics",
            "💳 Economics & SQL Workbench",
        ],
        label_visibility="collapsed",
    )
    st.sidebar.markdown("---")

    trips_df, zones_df, totals_dict = load_dashboard_data()

    if trips_df.empty:
        st.warning(
            "⚠️ No dataset found. Please run the pipeline ingestion step first: "
            "`python -m src.ingestion.download_taxi_data --year 2025 --months 1`"
        )
        st.stop()

    # Render Sidebar Filters & Return Filtered Dataset
    filtered_df = render_sidebar_filters(trips_df, zones_df)

    # Render Selected Page View
    if "Executive Overview" in selected_page:
        # Header Banner & KPI Cards ONLY on Main Page
        st.markdown(
            """
            <div class="main-header">
                <h1 class="main-header-title">🚕 NYC Yellow Taxi Executive Analytics</h1>
                <p class="main-header-subtitle">
                    Enterprise End-to-End Data Pipeline • PySpark Distributed Compute • PostgreSQL Data Warehouse
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_kpi_cards(filtered_df, totals_dict=totals_dict)
        st.markdown("<br>", unsafe_allow_html=True)
        render_demand_page(filtered_df)

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
        render_spatial_page(filtered_df)

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
        render_economics_page(filtered_df)


if __name__ == "__main__":
    main()
