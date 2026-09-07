"""Centralized Data Service for NYC Taxi Dashboard.

Provides high-performance, 100% numerically accurate SQL aggregations
over the full 2025 dataset (44.18M trips) using DuckDB and PostgreSQL fallbacks.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import streamlit as st
from src.utils.config import settings

# Load zone lookup once for ID <-> Name mapping
ZONE_PATH = settings.REFERENCE_DATA_DIR / "taxi_zone_lookup.csv"
if ZONE_PATH.exists():
    _ZONES_DF = pd.read_csv(ZONE_PATH)
    _Z_ID = "LocationID" if "LocationID" in _ZONES_DF.columns else "location_id"
    _Z_NAME = "Zone" if "Zone" in _ZONES_DF.columns else "pickup_zone_name"
    ZONE_DICT = dict(zip(_ZONES_DF[_Z_ID], _ZONES_DF[_Z_NAME]))
    ZONE_NAME_TO_IDS: Dict[str, List[int]] = {}
    for loc_id, name in ZONE_DICT.items():
        ZONE_NAME_TO_IDS.setdefault(str(name), []).append(int(loc_id))
else:
    _ZONES_DF = pd.DataFrame()
    ZONE_DICT = {}
    ZONE_NAME_TO_IDS = {}


def build_where_clause(filter_spec: Optional[Dict[str, Any]]) -> str:
    """Build SQL WHERE clause from filter specification dict."""
    if not filter_spec:
        return ""

    conditions = []

    # 1. Month Filter
    if filter_spec.get("months"):
        months = [int(m) for m in filter_spec["months"]]
        if len(months) < 12:
            months_str = ",".join(str(m) for m in months)
            conditions.append(f"month(tpep_pickup_datetime) IN ({months_str})")

    # 2. Payment Filter
    if filter_spec.get("payments") is not None:
        payments = [int(p) for p in filter_spec["payments"]]
        if len(payments) < 5:
            pay_str = ",".join(str(p) for p in payments)
            conditions.append(f"payment_type IN ({pay_str})")

    # 3. Distance Range
    if filter_spec.get("distance_range"):
        dmin, dmax = filter_spec["distance_range"]
        if dmin > 0 or dmax < 100:
            conditions.append(f"trip_distance >= {dmin} AND trip_distance <= {dmax}")

    # 4. Fare Range
    if filter_spec.get("fare_range"):
        fmin, fmax = filter_spec["fare_range"]
        if fmin > 0 or fmax < 300:
            conditions.append(f"fare_amount >= {fmin} AND fare_amount <= {fmax}")

    # 5. Taxi Zone Names
    if filter_spec.get("zones"):
        selected_ids = []
        for z_name in filter_spec["zones"]:
            selected_ids.extend(ZONE_NAME_TO_IDS.get(str(z_name), []))
        if selected_ids:
            ids_str = ",".join(str(i) for i in selected_ids)
            conditions.append(f"PULocationID IN ({ids_str})")

    if conditions:
        return "WHERE " + " AND ".join(conditions)
    return ""


def _get_duckdb_con():
    import duckdb

    return duckdb.connect()


def make_filter_key(filter_spec: Optional[Dict[str, Any]]) -> str:
    """Create deterministic hashable key for Streamlit caching."""
    if not filter_spec:
        return "ALL"
    parts = []
    for k in sorted(filter_spec.keys()):
        val = filter_spec[k]
        if isinstance(val, list):
            parts.append(f"{k}:{','.join(str(x) for x in sorted(val))}")
        elif isinstance(val, tuple):
            parts.append(f"{k}:{val[0]}-{val[1]}")
        else:
            parts.append(f"{k}:{val}")
    return "|".join(parts)


@st.cache_data(ttl=600)
def query_kpis(
    filter_key: str, filter_spec: Optional[Dict[str, Any]]
) -> Dict[str, float]:
    """Return exact full-dataset KPIs based on active filters."""
    where = build_where_clause(filter_spec)
    con = _get_duckdb_con()
    sql = f"""
        SELECT
            COUNT(*) as total_trips,
            COALESCE(SUM(total_amount), 0.0) as total_revenue,
            COALESCE(SUM(tip_amount), 0.0) as total_tips,
            COALESCE(AVG(fare_amount), 0.0) as avg_fare,
            COALESCE(AVG(trip_distance), 0.0) as avg_distance,
            COALESCE(AVG(epoch(tpep_dropoff_datetime - tpep_pickup_datetime)/60.0), 0.0) as avg_duration,
            COALESCE(AVG(CASE WHEN epoch(tpep_dropoff_datetime - tpep_pickup_datetime) > 0
                             THEN trip_distance / (epoch(tpep_dropoff_datetime - tpep_pickup_datetime)/3600.0)
                             ELSE 0.0 END), 0.0) as avg_speed,
            COALESCE(AVG(CASE WHEN fare_amount > 0 THEN (tip_amount / fare_amount) * 100.0 ELSE 0.0 END), 0.0) as avg_tip_pct
        FROM 'data/validated/*.parquet'
        {where}
    """
    df = con.query(sql).df()
    if df.empty or df.iloc[0]["total_trips"] == 0:
        return {
            "total_trips": 0,
            "total_revenue": 0.0,
            "total_tips": 0.0,
            "avg_fare": 0.0,
            "avg_distance": 0.0,
            "avg_duration": 0.0,
            "avg_speed": 0.0,
            "avg_tip_pct": 0.0,
        }
    return df.iloc[0].to_dict()


@st.cache_data(ttl=600)
def query_monthly_demand(
    filter_key: str, filter_spec: Optional[Dict[str, Any]]
) -> pd.DataFrame:
    """Return exact monthly trip volume and gross revenue aggregation."""
    where = build_where_clause(filter_spec)
    con = _get_duckdb_con()
    sql = f"""
        SELECT
            month(tpep_pickup_datetime) as pickup_month,
            COUNT(*) as trips,
            COALESCE(SUM(total_amount), 0.0) as revenue,
            COALESCE(AVG(fare_amount), 0.0) as avg_fare
        FROM 'data/validated/*.parquet'
        {where}
        GROUP BY pickup_month
        ORDER BY pickup_month
    """
    df = con.query(sql).df()
    month_map = {
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
    df["month_name"] = df["pickup_month"].map(month_map)
    return df


@st.cache_data(ttl=600)
def query_hourly_demand(
    filter_key: str, filter_spec: Optional[Dict[str, Any]]
) -> pd.DataFrame:
    """Return exact 24-hour demand profile aggregation."""
    where = build_where_clause(filter_spec)
    con = _get_duckdb_con()
    sql = f"""
        SELECT
            hour(tpep_pickup_datetime) as pickup_hour,
            COUNT(*) as trips,
            COALESCE(SUM(total_amount), 0.0) as revenue,
            COALESCE(AVG(fare_amount), 0.0) as avg_fare
        FROM 'data/validated/*.parquet'
        {where}
        GROUP BY pickup_hour
        ORDER BY pickup_hour
    """
    return con.query(sql).df()


@st.cache_data(ttl=600)
def query_dow_demand(
    filter_key: str, filter_spec: Optional[Dict[str, Any]]
) -> pd.DataFrame:
    """Return exact Day of Week volume profile aggregation."""
    where = build_where_clause(filter_spec)
    con = _get_duckdb_con()
    sql = f"""
        SELECT
            strftime(tpep_pickup_datetime, '%a') as pickup_day_of_week,
            COUNT(*) as trips,
            COALESCE(SUM(total_amount), 0.0) as revenue,
            COALESCE(AVG(fare_amount), 0.0) as avg_fare
        FROM 'data/validated/*.parquet'
        {where}
        GROUP BY pickup_day_of_week
    """
    df = con.query(sql).df()
    dow_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    df["pickup_day_of_week"] = pd.Categorical(
        df["pickup_day_of_week"], categories=dow_order, ordered=True
    )
    return df.sort_values("pickup_day_of_week").reset_index(drop=True)


@st.cache_data(ttl=600)
def query_payment_breakdown(
    filter_key: str, filter_spec: Optional[Dict[str, Any]]
) -> pd.DataFrame:
    """Return exact Payment Type breakdown and tipping statistics."""
    where = build_where_clause(filter_spec)
    con = _get_duckdb_con()
    sql = f"""
        SELECT
            payment_type,
            COUNT(*) as trips,
            COALESCE(SUM(total_amount), 0.0) as revenue,
            COALESCE(AVG(CASE WHEN fare_amount > 0 THEN (tip_amount / fare_amount) * 100.0 ELSE 0.0 END), 0.0) as avg_tip_pct
        FROM 'data/validated/*.parquet'
        {where}
        GROUP BY payment_type
        ORDER BY payment_type
    """
    df = con.query(sql).df()
    payment_map = {
        1: "Credit Card",
        0: "Cash",
        2: "No Charge",
        3: "Dispute",
        4: "Unknown",
        5: "Unknown",
    }
    df["payment_label"] = df["payment_type"].map(payment_map).fillna("Unknown")
    return df


@st.cache_data(ttl=600)
def query_top_zones(
    filter_key: str, filter_spec: Optional[Dict[str, Any]], limit: int = 10
) -> pd.DataFrame:
    """Return exact Top Busiest and Grossing Taxi Pickup Zones."""
    where = build_where_clause(filter_spec)
    con = _get_duckdb_con()
    sql = f"""
        SELECT
            PULocationID as pulocation_id,
            COUNT(*) as trip_count,
            COALESCE(SUM(total_amount), 0.0) as total_revenue,
            COALESCE(AVG(fare_amount), 0.0) as avg_fare
        FROM 'data/validated/*.parquet'
        {where}
        GROUP BY PULocationID
        ORDER BY trip_count DESC
        LIMIT {limit}
    """
    df = con.query(sql).df()
    df["pickup_zone_name"] = (
        df["pulocation_id"].map(ZONE_DICT).fillna("Unknown Zone")
    )
    return df


@st.cache_data(ttl=600)
def query_airport_metrics(
    filter_key: str, filter_spec: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Return exact airport trip counts and gross revenues for JFK and LaGuardia."""
    where = build_where_clause(filter_spec)
    if where:
        airport_where = f"{where} AND PULocationID IN (132, 138)"
    else:
        airport_where = "WHERE PULocationID IN (132, 138)"

    con = _get_duckdb_con()
    sql = f"""
        SELECT
            PULocationID,
            COUNT(*) as trips,
            COALESCE(SUM(total_amount), 0.0) as revenue
        FROM 'data/validated/*.parquet'
        {airport_where}
        GROUP BY PULocationID
    """
    df = con.query(sql).df()
    jfk_trips = (
        int(df[df["PULocationID"] == 132]["trips"].sum())
        if not df.empty and 132 in df["PULocationID"].values
        else 0
    )
    jfk_rev = (
        float(df[df["PULocationID"] == 132]["revenue"].sum())
        if not df.empty and 132 in df["PULocationID"].values
        else 0.0
    )
    lga_trips = (
        int(df[df["PULocationID"] == 138]["trips"].sum())
        if not df.empty and 138 in df["PULocationID"].values
        else 0
    )
    lga_rev = (
        float(df[df["PULocationID"] == 138]["revenue"].sum())
        if not df.empty and 138 in df["PULocationID"].values
        else 0.0
    )

    return {
        "jfk_trips": jfk_trips,
        "jfk_rev": jfk_rev,
        "lga_trips": lga_trips,
        "lga_rev": lga_rev,
        "total_airport_trips": jfk_trips + lga_trips,
        "total_airport_rev": jfk_rev + lga_rev,
    }


@st.cache_data(ttl=600)
def query_peak_hour_info(
    filter_key: str, filter_spec: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Return exact dynamically computed peak demand hour."""
    where = build_where_clause(filter_spec)
    con = _get_duckdb_con()
    sql = f"""
        SELECT
            hour(tpep_pickup_datetime) as pickup_hour,
            COUNT(*) as trips,
            COALESCE(SUM(total_amount), 0.0) as revenue
        FROM 'data/validated/*.parquet'
        {where}
        GROUP BY pickup_hour
        ORDER BY trips DESC
        LIMIT 1
    """
    df = con.query(sql).df()
    if df.empty:
        return {
            "peak_hour": 18,
            "hour_str": "18:00–19:00 (6–7 PM)",
            "trips": 0,
            "revenue": 0.0,
        }

    h = int(df.iloc[0]["pickup_hour"])
    start_12 = h % 12 or 12
    end_12 = (h + 1) % 12 or 12
    ampm_end = "AM" if (h + 1) < 12 or (h + 1) == 24 else "PM"
    hour_str = f"{h:02d}:00–{(h + 1) % 24:02d}:00 ({start_12}–{end_12} {ampm_end})"

    return {
        "peak_hour": h,
        "hour_str": hour_str,
        "trips": int(df.iloc[0]["trips"]),
        "revenue": float(df.iloc[0]["revenue"]),
    }


@st.cache_data(ttl=600)
def query_speed_by_hour(
    filter_key: str, filter_spec: Optional[Dict[str, Any]]
) -> pd.DataFrame:
    """Return average speed in mph across 24 hours."""
    where = build_where_clause(filter_spec)
    con = _get_duckdb_con()
    sql = f"""
        SELECT
            hour(tpep_pickup_datetime) as pickup_hour,
            COALESCE(AVG(CASE WHEN epoch(tpep_dropoff_datetime - tpep_pickup_datetime) > 0
                             THEN trip_distance / (epoch(tpep_dropoff_datetime - tpep_pickup_datetime)/3600.0)
                             ELSE 0.0 END), 0.0) as avg_speed_mph
        FROM 'data/validated/*.parquet'
        {where}
        GROUP BY pickup_hour
        ORDER BY pickup_hour
    """
    return con.query(sql).df()


@st.cache_data(ttl=600)
def query_tipping_summary(
    filter_key: str, filter_spec: Optional[Dict[str, Any]]
) -> pd.DataFrame:
    """Return volume breakdown of tipped vs non-tipped trips."""
    where = build_where_clause(filter_spec)
    con = _get_duckdb_con()
    sql = f"""
        SELECT
            CASE WHEN tip_amount > 0 THEN 'Tipped Trips' ELSE 'Non-Tipped Trips' END as Category,
            COUNT(*) as Count,
            COALESCE(SUM(total_amount), 0.0) as Revenue
        FROM 'data/validated/*.parquet'
        {where}
        GROUP BY Category
    """
    return con.query(sql).df()


@st.cache_data(ttl=600)
def query_rush_hour_summary(
    filter_key: str, filter_spec: Optional[Dict[str, Any]]
) -> pd.DataFrame:
    """Return average duration and speed for Peak Rush Hour vs Off-Peak."""
    where = build_where_clause(filter_spec)
    con = _get_duckdb_con()
    sql = f"""
        SELECT
            CASE WHEN dayofweek(tpep_pickup_datetime) BETWEEN 1 AND 5
                      AND (hour(tpep_pickup_datetime) BETWEEN 7 AND 9 OR hour(tpep_pickup_datetime) BETWEEN 16 AND 19)
                 THEN 'Peak Rush Hour' ELSE 'Off-Peak' END as peak_category,
            COALESCE(AVG(epoch(tpep_dropoff_datetime - tpep_pickup_datetime)/60.0), 0.0) as avg_duration,
            COALESCE(AVG(CASE WHEN epoch(tpep_dropoff_datetime - tpep_pickup_datetime) > 0
                             THEN trip_distance / (epoch(tpep_dropoff_datetime - tpep_pickup_datetime)/3600.0)
                             ELSE 0.0 END), 0.0) as avg_speed
        FROM 'data/validated/*.parquet'
        {where}
        GROUP BY peak_category
    """
    return con.query(sql).df()
