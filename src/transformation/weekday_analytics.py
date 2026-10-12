"""Weekday Analytics Module.

Provides mathematical and calendar-aware aggregations for weekday mobility metrics.
Normalizes trip volumes by distinct calendar date occurrences to prevent calendar skew.
"""

import calendar
from collections import Counter
from typing import Any, Dict, List, Optional
import pandas as pd


def get_calendar_day_counts(
    year: int = 2025, months: Optional[List[int]] = None
) -> Dict[str, int]:
    """Calculate the exact number of occurrences for each day of the week in given months.

    Args:
        year: Target calendar year (e.g., 2025).
        months: List of 1-based months (1..12). Defaults to all 12 months.

    Returns:
        Dict mapping abbreviated weekday ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')
        to the count of calendar dates that day occurred on.
    """
    if not months:
        months = list(range(1, 13))

    dow_map = {0: "Mon", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 5: "Sat", 6: "Sun"}
    counts = Counter({d: 0 for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]})

    for m in months:
        num_days = calendar.monthrange(year, m)[1]
        for d in range(1, num_days + 1):
            dow = calendar.weekday(year, m, d)
            counts[dow_map[dow]] += 1

    return dict(counts)


def calculate_weekday_aggregations(
    daily_df: pd.DataFrame,
    date_col: str = "pickup_date",
    weekday_col: str = "pickup_day_of_week",
    trips_col: str = "total_trips",
    revenue_col: str = "total_revenue",
    fare_col: str = "avg_fare",
) -> pd.DataFrame:
    """Aggregate daily records into weekday performance summaries with date normalization.

    Args:
        daily_df: DataFrame with daily rows (one row per calendar date or grouped daily).
        date_col: Column name containing the date or timestamp.
        weekday_col: Column name containing weekday string ('Mon', 'Tue', etc.).
        trips_col: Column name containing trip count.
        revenue_col: Column name containing total revenue.
        fare_col: Column name containing average or itemized fare.

    Returns:
        DataFrame sorted by day of week with columns:
        - pickup_day_of_week
        - calendar_days
        - total_trips
        - avg_trips_per_day
        - total_revenue
        - avg_revenue_per_day
        - avg_fare
    """
    dow_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    grouped = (
        daily_df.groupby(weekday_col)
        .agg(
            calendar_days=(date_col, "nunique"),
            total_trips=(trips_col, "sum"),
            total_revenue=(revenue_col, "sum"),
            avg_fare=(
                (fare_col, "mean")
                if fare_col in daily_df.columns
                else (trips_col, "count")
            ),
        )
        .reset_index()
    )

    grouped["calendar_days"] = grouped["calendar_days"].replace(0, 1)
    grouped["avg_trips_per_day"] = (
        grouped["total_trips"] / grouped["calendar_days"]
    ).round(2)
    grouped["avg_revenue_per_day"] = (
        grouped["total_revenue"] / grouped["calendar_days"]
    ).round(2)
    if fare_col in daily_df.columns:
        grouped["avg_fare"] = grouped["avg_fare"].round(2)

    grouped[weekday_col] = pd.Categorical(
        grouped[weekday_col], categories=dow_order, ordered=True
    )
    return grouped.sort_values(weekday_col).reset_index(drop=True)


def compare_weekdays(
    stats_df: pd.DataFrame,
    day_a: str = "Thu",
    day_b: str = "Mon",
    weekday_col: str = "pickup_day_of_week",
) -> Dict[str, Any]:
    """Compare mobility volume between two weekdays reporting both total and normalized metrics.

    Args:
        stats_df: Aggregated weekday DataFrame with total_trips and avg_trips_per_day.
        day_a: First weekday abbreviation to compare.
        day_b: Baseline weekday abbreviation to compare against.
        weekday_col: Column identifying weekday.

    Returns:
        Dict detailing raw vs date-normalized differences, percentage changes, and interpretation.
    """
    row_a = stats_df[stats_df[weekday_col] == day_a]
    row_b = stats_df[stats_df[weekday_col] == day_b]

    if row_a.empty or row_b.empty:
        raise ValueError(
            f"One or both weekdays ('{day_a}', '{day_b}') not found in dataset."
        )

    trips_a = float(row_a.iloc[0]["total_trips"])
    trips_b = float(row_b.iloc[0]["total_trips"])
    days_a = int(row_a.iloc[0]["calendar_days"])
    days_b = int(row_b.iloc[0]["calendar_days"])
    avg_a = float(row_a.iloc[0]["avg_trips_per_day"])
    avg_b = float(row_b.iloc[0]["avg_trips_per_day"])

    total_diff = trips_a - trips_b
    total_pct_diff = (total_diff / trips_b) * 100.0 if trips_b > 0 else 0.0

    avg_diff = avg_a - avg_b
    avg_pct_diff = (avg_diff / avg_b) * 100.0 if avg_b > 0 else 0.0

    calendar_ratio = days_a / days_b if days_b > 0 else 1.0

    explanation = (
        f"{day_a} recorded {total_pct_diff:.2f}% higher total trips than {day_b} "
        f"({trips_a:,.0f} vs {trips_b:,.0f}). However, {day_a} occurred on {days_a} calendar dates "
        f"whereas {day_b} occurred on {days_b} calendar dates ({calendar_ratio:.2f}x multiplier). "
        f"Normalized on an average-per-calendar-date basis, {day_a} averaged {avg_a:,.2f} trips/day "
        f"vs {avg_b:,.2f} trips/day for {day_b}, representing a true daily demand increase of {avg_pct_diff:.2f}%."
    )

    return {
        "day_a": day_a,
        "day_b": day_b,
        "day_a_total_trips": trips_a,
        "day_b_total_trips": trips_b,
        "total_trips_diff": total_diff,
        "total_trips_pct_diff": round(total_pct_diff, 2),
        "day_a_calendar_days": days_a,
        "day_b_calendar_days": days_b,
        "calendar_ratio": round(calendar_ratio, 2),
        "day_a_avg_daily_trips": avg_a,
        "day_b_avg_daily_trips": avg_b,
        "avg_daily_trips_diff": round(avg_diff, 2),
        "avg_daily_trips_pct_diff": round(avg_pct_diff, 2),
        "explanation": explanation,
    }
