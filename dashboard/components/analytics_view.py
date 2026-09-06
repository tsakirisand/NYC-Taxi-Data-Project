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
            "Month Revenue Summary (2025)": (
                "SELECT pickup_year, pickup_month, COUNT(*) as trip_count, "
                "ROUND(SUM(total_amount), 2) as total_revenue_usd "
                "FROM fact_trips WHERE pickup_year = 2025 "
                "GROUP BY pickup_year, pickup_month ORDER BY total_revenue_usd DESC"
            ),
            "Top 10 Busiest Routes": (
                "SELECT pz.zone as pickup_zone, dz.zone as dropoff_zone, COUNT(*) as trip_count, "
                "ROUND(AVG(f.fare_amount), 2) as avg_fare_usd FROM fact_trips f "
                "JOIN dim_taxi_zone pz ON f.pulocation_id = pz.location_id "
                "JOIN dim_taxi_zone dz ON f.dolocation_id = dz.location_id "
                "WHERE f.pickup_year = 2025 "
                "GROUP BY pz.zone, dz.zone ORDER BY trip_count DESC LIMIT 10"
            ),
            "Tip Propensity Statistics": (
                "SELECT COUNT(*) as total_trips, "
                "SUM(CASE WHEN tip_amount > 0 THEN 1 ELSE 0 END) as tipped_trips, "
                "ROUND(AVG(tip_percentage), 2) as avg_tip_pct "
                "FROM fact_trips WHERE pickup_year = 2025"
            ),
            "Airport Trips Analysis": (
                "SELECT CASE WHEN rate_code_id = 2 THEN 'JFK Airport' "
                "WHEN rate_code_id = 3 THEN 'Newark Airport' ELSE 'City Trip' END as category, "
                "COUNT(*) as trip_count, ROUND(AVG(fare_amount), 2) as avg_fare_usd "
                "FROM fact_trips WHERE pickup_year = 2025 GROUP BY category ORDER BY trip_count DESC"
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
    st.markdown("#### 📋 Clean Formatted Trip Records Preview")

    if not df.empty:
        # Prepare readable preview DataFrame
        preview_df = df.copy()

        # Select key columns for clean presentation
        cols_to_show = []
        col_rename = {}

        if "pickup_zone_name" in preview_df.columns:
            cols_to_show.append("pickup_zone_name")
            col_rename["pickup_zone_name"] = "Pickup Zone"

        if "trip_duration_minutes" in preview_df.columns:
            cols_to_show.append("trip_duration_minutes")
            col_rename["trip_duration_minutes"] = "Duration (min)"

        if "avg_speed_mph" in preview_df.columns:
            cols_to_show.append("avg_speed_mph")
            col_rename["avg_speed_mph"] = "Avg Speed (mph)"

        if "fare_amount" in preview_df.columns:
            cols_to_show.append("fare_amount")
            col_rename["fare_amount"] = "Fare ($)"

        if "total_amount" in preview_df.columns:
            cols_to_show.append("total_amount")
            col_rename["total_amount"] = "Total ($)"

        if "tip_percentage" in preview_df.columns:
            cols_to_show.append("tip_percentage")
            col_rename["tip_percentage"] = "Tip (%)"

        if "pickup_hour" in preview_df.columns:
            cols_to_show.append("pickup_hour")
            col_rename["pickup_hour"] = "Hour of Day"

        if "pickup_day_of_week" in preview_df.columns:
            cols_to_show.append("pickup_day_of_week")
            col_rename["pickup_day_of_week"] = "Day of Week"

        if "rush_hour_status" in preview_df.columns:
            cols_to_show.append("rush_hour_status")
            col_rename["rush_hour_status"] = "Rush Hour Category"
        elif "is_peak_hour" in preview_df.columns:
            preview_df["rush_hour_status"] = (
                preview_df["is_peak_hour"]
                .map(
                    {
                        1: "🔥 Peak Rush Hour",
                        0: "🌙 Off-Peak",
                        "1": "🔥 Peak Rush Hour",
                        "0": "🌙 Off-Peak",
                    }
                )
                .fillna("🌙 Off-Peak")
            )
            cols_to_show.append("rush_hour_status")
            col_rename["rush_hour_status"] = "Rush Hour Category"

        display_df = preview_df[cols_to_show].rename(columns=col_rename)

        # Allow user to pick sample size or filter by peak hour
        filter_col1, filter_col2 = st.columns([1, 2])
        with filter_col1:
            hour_filter = st.selectbox(
                "Filter Sample by Hour",
                options=["All Hours"] + [f"Hour {h}:00" for h in range(24)],
            )
        with filter_col2:
            st.caption(
                "Displaying cleaned sample records with peak hour categories and readable zone names."
            )

        if hour_filter != "All Hours":
            target_h = int(hour_filter.split()[1].split(":")[0])
            display_df = display_df[display_df["Hour of Day"] == target_h]

        st.dataframe(display_df.head(50), use_container_width=True)
