"""Unit tests for Weekday Analytics and Calendar Normalization."""

import pytest
import pandas as pd
from src.transformation.weekday_analytics import (
    get_calendar_day_counts,
    calculate_weekday_aggregations,
    compare_weekdays,
)


def test_calendar_day_counts_january_2025():
    """Verify that January 2025 calendar days have 5 Thursdays/Fridays/Wednesdays and 4 of other weekdays."""
    counts = get_calendar_day_counts(2025, [1])

    assert counts["Thu"] == 5
    assert counts["Fri"] == 5
    assert counts["Wed"] == 5
    assert counts["Mon"] == 4
    assert counts["Tue"] == 4
    assert counts["Sat"] == 4
    assert counts["Sun"] == 4
    assert sum(counts.values()) == 31


def test_calendar_day_counts_full_year_2025():
    """Verify that full-year 2025 has 53 Wednesdays and 52 of each other day (365 total days)."""
    counts = get_calendar_day_counts(2025)

    assert counts["Wed"] == 53
    for day in ["Mon", "Tue", "Thu", "Fri", "Sat", "Sun"]:
        assert counts[day] == 52
    assert sum(counts.values()) == 365


def test_weekday_aggregation_totals_and_averages():
    """Verify that daily trip records aggregate correctly to weekday totals and date averages."""
    # Synthetic daily records: 2 Thursdays (10 trips each = 20 total) and 1 Monday (10 trips = 10 total)
    daily_data = pd.DataFrame(
        [
            {
                "pickup_date": "2025-01-02",
                "pickup_day_of_week": "Thu",
                "total_trips": 10,
                "total_revenue": 200.0,
                "avg_fare": 20.0,
            },
            {
                "pickup_date": "2025-01-09",
                "pickup_day_of_week": "Thu",
                "total_trips": 10,
                "total_revenue": 200.0,
                "avg_fare": 20.0,
            },
            {
                "pickup_date": "2025-01-06",
                "pickup_day_of_week": "Mon",
                "total_trips": 10,
                "total_revenue": 200.0,
                "avg_fare": 20.0,
            },
        ]
    )

    agg_df = calculate_weekday_aggregations(daily_data)

    thu_row = agg_df[agg_df["pickup_day_of_week"] == "Thu"].iloc[0]
    mon_row = agg_df[agg_df["pickup_day_of_week"] == "Mon"].iloc[0]

    assert thu_row["calendar_days"] == 2
    assert thu_row["total_trips"] == 20
    assert thu_row["avg_trips_per_day"] == 10.0

    assert mon_row["calendar_days"] == 1
    assert mon_row["total_trips"] == 10
    assert mon_row["avg_trips_per_day"] == 10.0


def test_thursday_vs_monday_january_2025_empirical_verification():
    """Verify the README's claim that Thursday had 571.7K trips (+66.4% vs Monday total)
    and verify the normalized per-date average (+33.14%)."""
    stats_df = pd.DataFrame(
        [
            {
                "pickup_day_of_week": "Thu",
                "calendar_days": 5,
                "total_trips": 571720,
                "avg_trips_per_day": 114344.0,
            },
            {
                "pickup_day_of_week": "Mon",
                "calendar_days": 4,
                "total_trips": 343539,
                "avg_trips_per_day": 85884.75,
            },
        ]
    )

    comp = compare_weekdays(stats_df, day_a="Thu", day_b="Mon")

    # 1. Raw aggregate monthly totals comparison:
    # (571,720 - 343,539) / 343,539 = 66.42%
    assert comp["total_trips_pct_diff"] == 66.42
    assert comp["total_trips_diff"] == 228181

    # 2. Calendar day occurrence ratio: 5 Thursdays / 4 Mondays = 1.25x
    assert comp["calendar_ratio"] == 1.25

    # 3. Date-normalized daily average comparison:
    # (114,344.0 - 85,884.75) / 85,884.75 = 33.14%
    assert comp["avg_daily_trips_pct_diff"] == 33.14
    assert comp["day_a_avg_daily_trips"] == 114344.0
    assert comp["day_b_avg_daily_trips"] == 85884.75


def test_compare_weekdays_equal_daily_demand():
    """Verify that when daily demand is identical, total trips differ solely due to calendar dates."""
    stats_df = pd.DataFrame(
        [
            {
                "pickup_day_of_week": "Thu",
                "calendar_days": 5,
                "total_trips": 500,
                "avg_trips_per_day": 100.0,
            },
            {
                "pickup_day_of_week": "Mon",
                "calendar_days": 4,
                "total_trips": 400,
                "avg_trips_per_day": 100.0,
            },
        ]
    )

    comp = compare_weekdays(stats_df, day_a="Thu", day_b="Mon")

    # Raw total differs by +25% because 5 dates vs 4 dates
    assert comp["total_trips_pct_diff"] == 25.0
    # Normalized daily average shows 0.0% difference (identical daily demand)
    assert comp["avg_daily_trips_pct_diff"] == 0.0


def test_compare_weekdays_missing_day_raises_error():
    """Verify that comparing a non-existent weekday raises ValueError."""
    stats_df = pd.DataFrame(
        [
            {
                "pickup_day_of_week": "Thu",
                "calendar_days": 5,
                "total_trips": 500,
                "avg_trips_per_day": 100.0,
            }
        ]
    )

    with pytest.raises(ValueError):
        compare_weekdays(stats_df, day_a="Thu", day_b="Mon")
