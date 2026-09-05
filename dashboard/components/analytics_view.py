"""SQL Analytics Query Runner & Raw Data Explorer Component."""

import pandas as pd
import streamlit as st
from sqlalchemy import text
from src.database.load_postgres import DatabaseLoader


def render_analytics_tab(df: pd.DataFrame):
    """Render raw dataset preview and interactive SQL query runner."""
    st.subheader("💾 Interactive SQL Query Runner & Data Explorer")

    c1, c2 = st.columns([1, 1])

    with c1:
        st.markdown("#### ⚡ Preset Analytical Queries")
        query_options = {
            "Month with Most Revenue": (
                "SELECT pickup_year, pickup_month, ROUND(SUM(total_amount), 2) as total_revenue "
                "FROM fact_trips GROUP BY pickup_year, pickup_month ORDER BY total_revenue DESC LIMIT 5"
            ),
            "Top 10 Busiest Routes": (
                "SELECT pz.zone as pickup_zone, dz.zone as dropoff_zone, COUNT(*) as trip_count, "
                "ROUND(AVG(f.fare_amount), 2) as avg_fare FROM fact_trips f "
                "JOIN dim_taxi_zone pz ON f.pulocation_id = pz.location_id "
                "JOIN dim_taxi_zone dz ON f.dolocation_id = dz.location_id "
                "GROUP BY pz.zone, dz.zone ORDER BY trip_count DESC LIMIT 10"
            ),
            "Tip Propensity Statistics": (
                "SELECT COUNT(*) as total_trips, SUM(CASE WHEN tip_amount > 0 THEN 1 ELSE 0 END) as tipped_trips, "
                "ROUND(AVG(tip_percentage), 2) as avg_tip_pct FROM fact_trips"
            ),
            "Airport Trips Analysis": (
                "SELECT CASE WHEN rate_code_id = 2 THEN 'JFK Airport' WHEN rate_code_id = 3 THEN 'Newark Airport' "
                "ELSE 'City Trip' END as category, COUNT(*) as trip_count, ROUND(AVG(fare_amount), 2) as avg_fare "
                "FROM fact_trips GROUP BY category ORDER BY trip_count DESC"
            ),
        }

        selected_preset = st.selectbox(
            "Select Preset SQL Query", list(query_options.keys())
        )
        default_sql = query_options[selected_preset]

    with c2:
        st.markdown("#### ✍️ SQL Editor")
        sql_input = st.text_area("SQL Query", value=default_sql, height=120)

    if st.button("🚀 Execute SQL Query", type="primary"):
        loader = DatabaseLoader()
        try:
            with loader.engine.connect() as conn:
                result_df = pd.read_sql(text(sql_input), con=conn)
            st.success(f"Query executed successfully! Returned {len(result_df)} rows.")
            st.dataframe(result_df, use_container_width=True)
        except Exception as e:
            st.error(f"SQL Execution Error: {e}")

    st.markdown("---")
    st.markdown("#### 📋 Raw Sample Records")
    st.dataframe(df.head(100), use_container_width=True)
