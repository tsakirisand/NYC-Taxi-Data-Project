"""NYC Yellow Taxi Data Engineering - Interactive Analytics Portal.

Modular Streamlit Dashboard entrypoint separating features across sidebar control panel
and 5 dedicated analytical tabs.
"""

import sys
from pathlib import Path

# Ensure root package path resolution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from dashboard.components.analytics_view import render_analytics_tab  # noqa: E402
from dashboard.components.demand_charts import render_demand_tab  # noqa: E402
from dashboard.components.economics_charts import render_economics_tab  # noqa: E402
from dashboard.components.kpis import render_kpi_cards  # noqa: E402
from dashboard.components.sidebar import render_sidebar_filters  # noqa: E402
from dashboard.components.spatial_charts import render_spatial_tab  # noqa: E402
from dashboard.components.temporal_charts import render_temporal_tab  # noqa: E402
from dashboard.styles import inject_custom_css  # noqa: E402
from src.database.load_postgres import DatabaseLoader  # noqa: E402
from src.utils.config import settings  # noqa: E402

# 1. Page Configuration
st.set_page_config(
    page_title="NYC Yellow Taxi Data Engineering",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 2. Inject Custom Theme & Design System
inject_custom_css()


@st.cache_data(ttl=300)
def load_dashboard_data():
    """Load fact trips and taxi zone lookup tables from DB or Parquet fallback."""
    loader = DatabaseLoader()
    engine = loader.engine

    try:
        trips_df = pd.read_sql(
            """
            SELECT f.*, z.zone as pickup_zone_name, z.borough as pickup_borough
            FROM fact_trips f
            LEFT JOIN dim_taxi_zone z ON f.pulocation_id = z.location_id
            """,
            con=engine,
        )
        zones_df = pd.read_sql("SELECT * FROM dim_taxi_zone", con=engine)
    except Exception:
        # Fallback to local Parquet files if DB table not yet populated
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

    return trips_df, zones_df


def main():
    # Header Glassmorphism Banner
    st.markdown(
        """
        <div class="main-header">
            <h1 class="main-header-title">🚕 NYC Yellow Taxi Analytics Portal</h1>
            <p class="main-header-subtitle">
                Enterprise End-to-End Data Pipeline • PySpark Distributed Compute • PostgreSQL Data Warehouse
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    trips_df, zones_df = load_dashboard_data()

    if trips_df.empty:
        st.warning(
            "⚠️ No dataset found. Please run the pipeline ingestion step first: "
            "`python -m src.ingestion.download_taxi_data --year 2025 --months 1`"
        )
        st.stop()

    # Render Sidebar Controls & Return Filtered Dataset
    filtered_df = render_sidebar_filters(trips_df, zones_df)

    # Render Top KPI Cards Row
    render_kpi_cards(filtered_df)

    st.markdown("<br>", unsafe_allow_html=True)

    # Render 5 Separated Feature Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        [
            "📊 Executive Overview",
            "📍 Spatial & Zone Analytics",
            "💳 Trip Economics & Payments",
            "⏱️ Temporal & Speed Insights",
            "💻 SQL Workbench & Data Explorer",
        ]
    )

    with tab1:
        render_demand_tab(filtered_df)

    with tab2:
        render_spatial_tab(filtered_df)

    with tab3:
        render_economics_tab(filtered_df)

    with tab4:
        render_temporal_tab(filtered_df)

    with tab5:
        render_analytics_tab(filtered_df)


if __name__ == "__main__":
    main()
