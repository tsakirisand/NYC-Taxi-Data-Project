"""Unit tests for Key Analytical Metric Definitions and Calculations."""

import pandas as pd
import numpy as np


def compute_trip_duration(pickup: pd.Series, dropoff: pd.Series) -> pd.Series:
    """Calculate trip duration in minutes."""
    diff = pd.to_datetime(dropoff) - pd.to_datetime(pickup)
    if hasattr(diff, "dt"):
        secs = diff.dt.total_seconds()
    else:
        secs = diff.total_seconds()
    return (pd.Series(secs) / 60.0).round(2)


def compute_avg_speed(distance: pd.Series, duration_minutes: pd.Series) -> pd.Series:
    """Calculate average speed in miles per hour with zero-duration protection."""
    hours = duration_minutes / 60.0
    speed = np.where(duration_minutes > 0, distance / hours, 0.0)
    return pd.Series(speed, index=distance.index).round(2)


def compute_tip_percentage(tip: pd.Series, fare: pd.Series) -> pd.Series:
    """Calculate tip percentage based on base fare with zero-fare protection."""
    tip_pct = np.where(fare > 0, (tip / fare) * 100.0, 0.0)
    return pd.Series(tip_pct, index=tip.index).round(2)


def compute_is_peak_hour(timestamps: pd.Series) -> pd.Series:
    """Determine if trip occurred during weekday NYC peak rush hours (07-09, 16-19)."""
    ts = pd.Series(pd.to_datetime(timestamps))
    dow = ts.dt.dayofweek  # 0=Mon, 4=Fri, 5=Sat, 6=Sun
    hours = ts.dt.hour
    is_weekday = dow.between(0, 4)
    is_rush_window = hours.between(7, 9) | hours.between(16, 19)
    return is_weekday & is_rush_window


def test_trip_duration_calculation():
    """Verify trip duration formula."""
    pickups = pd.Series(pd.to_datetime(["2025-01-15 08:00:00", "2025-01-15 08:30:00"]))
    dropoffs = pd.Series(pd.to_datetime(["2025-01-15 08:15:30", "2025-01-15 09:00:00"]))

    durations = compute_trip_duration(pickups, dropoffs)
    assert durations.iloc[0] == 15.5  # 15 mins 30 secs
    assert durations.iloc[1] == 30.0  # 30 mins


def test_average_speed_calculation():
    """Verify velocity computation in mph and division-by-zero handling."""
    distances = pd.Series([5.0, 10.0, 3.0])
    durations = pd.Series([15.0, 30.0, 0.0])  # 15m = 0.25h, 30m = 0.5h, 0m

    speeds = compute_avg_speed(distances, durations)
    assert speeds.iloc[0] == 20.0  # 5 mi / 0.25 h = 20 mph
    assert speeds.iloc[1] == 20.0  # 10 mi / 0.5 h = 20 mph
    assert speeds.iloc[2] == 0.0  # 0 duration yields 0 mph without error


def test_tip_percentage_calculation():
    """Verify tip percentage based on base fare amount."""
    tips = pd.Series([3.0, 0.0, 5.0, 2.0])
    fares = pd.Series([15.0, 20.0, 25.0, 0.0])

    tip_pcts = compute_tip_percentage(tips, fares)
    assert tip_pcts.iloc[0] == 20.0  # $3 on $15 = 20%
    assert tip_pcts.iloc[1] == 0.0  # $0 tip = 0%
    assert tip_pcts.iloc[2] == 20.0  # $5 on $25 = 20%
    assert tip_pcts.iloc[3] == 0.0  # $0 fare yields 0% without error


def test_peak_hour_classification():
    """Verify weekday rush hour classification logic."""
    # 2025-01-15 is Wednesday (weekday)
    # 2025-01-18 is Saturday (weekend)
    timestamps = pd.to_datetime(
        [
            "2025-01-15 08:30:00",  # Wed morning rush -> True
            "2025-01-15 12:00:00",  # Wed midday -> False
            "2025-01-15 17:45:00",  # Wed evening rush -> True
            "2025-01-15 22:00:00",  # Wed night -> False
            "2025-01-18 08:30:00",  # Sat morning (weekend) -> False
            "2025-01-18 17:45:00",  # Sat evening (weekend) -> False
        ]
    )

    peak_flags = compute_is_peak_hour(timestamps)
    assert peak_flags.tolist() == [True, False, True, False, False, False]


def test_tipping_propensity_metrics():
    """Verify overall tip rate vs credit card tip rate and percent tipped trips."""
    trips_df = pd.DataFrame(
        [
            {
                "payment_type": 1,
                "fare_amount": 20.0,
                "tip_amount": 5.0,
            },  # Credit card tipped (25%)
            {
                "payment_type": 1,
                "fare_amount": 20.0,
                "tip_amount": 0.0,
            },  # Credit card untipped (0%)
            {
                "payment_type": 2,
                "fare_amount": 20.0,
                "tip_amount": 0.0,
            },  # Cash untipped (0%)
            {
                "payment_type": 2,
                "fare_amount": 20.0,
                "tip_amount": 0.0,
            },  # Cash untipped (0%)
        ]
    )

    total_trips = len(trips_df)
    tipped_trips = (trips_df["tip_amount"] > 0).sum()
    pct_trips_tipped = (tipped_trips / total_trips) * 100.0

    cc_trips = trips_df[trips_df["payment_type"] == 1]
    cc_tip_rate = (cc_trips["tip_amount"] / cc_trips["fare_amount"] * 100.0).mean()

    overall_tip_rate = (trips_df["tip_amount"] / trips_df["fare_amount"] * 100.0).mean()

    assert pct_trips_tipped == 25.0  # 1 out of 4 trips tipped
    assert cc_tip_rate == 12.5  # average of 25% and 0% for credit card
    assert overall_tip_rate == 6.25  # average across all 4 trips
