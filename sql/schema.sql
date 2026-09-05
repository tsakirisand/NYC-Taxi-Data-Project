-- NYC Taxi Data Engineering - Relational Schema DDL
-- Compatible with PostgreSQL & SQLite

-- 1. Taxi Zone Dimension Table
CREATE TABLE IF NOT EXISTS dim_taxi_zone (
    location_id INTEGER PRIMARY KEY,
    borough VARCHAR(50) NOT NULL,
    zone VARCHAR(100) NOT NULL,
    service_zone VARCHAR(50)
);

-- 2. Date Dimension Table
CREATE TABLE IF NOT EXISTS dim_date (
    date_key DATE PRIMARY KEY,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    day INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    is_weekend BOOLEAN NOT NULL,
    quarter INTEGER NOT NULL
);

-- 3. Fact Trips Table
CREATE TABLE IF NOT EXISTS fact_trips (
    trip_id VARCHAR(64) PRIMARY KEY,
    vendor_id INTEGER,
    tpep_pickup_datetime TIMESTAMP NOT NULL,
    tpep_dropoff_datetime TIMESTAMP NOT NULL,
    passenger_count INTEGER,
    trip_distance NUMERIC(10, 2) NOT NULL,
    rate_code_id INTEGER,
    store_and_fwd_flag VARCHAR(5),
    pulocation_id INTEGER REFERENCES dim_taxi_zone(location_id),
    dolocation_id INTEGER REFERENCES dim_taxi_zone(location_id),
    payment_type INTEGER,
    fare_amount NUMERIC(10, 2) NOT NULL,
    extra NUMERIC(10, 2),
    mta_tax NUMERIC(10, 2),
    tip_amount NUMERIC(10, 2),
    tolls_amount NUMERIC(10, 2),
    improvement_surcharge NUMERIC(10, 2),
    total_amount NUMERIC(10, 2) NOT NULL,
    congestion_surcharge NUMERIC(10, 2),
    airport_fee NUMERIC(10, 2),
    
    -- Calculated features
    trip_duration_minutes NUMERIC(10, 2),
    avg_speed_mph NUMERIC(10, 2),
    tip_percentage NUMERIC(10, 2),
    pickup_date DATE,
    pickup_hour INTEGER,
    pickup_day_of_week VARCHAR(10),
    is_peak_hour BOOLEAN
);

-- 4. Aggregate Hourly Summary Table
CREATE TABLE IF NOT EXISTS agg_hourly_trips (
    pickup_hour INTEGER PRIMARY KEY,
    total_trips BIGINT NOT NULL,
    total_revenue NUMERIC(14, 2) NOT NULL,
    avg_fare NUMERIC(10, 2),
    avg_distance NUMERIC(10, 2),
    avg_duration NUMERIC(10, 2),
    avg_tip_percentage NUMERIC(10, 2)
);

-- 5. Aggregate Daily Summary Table
CREATE TABLE IF NOT EXISTS agg_daily_trips (
    pickup_date DATE PRIMARY KEY,
    pickup_day_of_week VARCHAR(10),
    total_trips BIGINT NOT NULL,
    total_revenue NUMERIC(14, 2) NOT NULL,
    avg_fare NUMERIC(10, 2),
    avg_distance NUMERIC(10, 2)
);

-- 6. Aggregate Monthly Summary Table
CREATE TABLE IF NOT EXISTS agg_monthly_summary (
    pickup_year INTEGER,
    pickup_month INTEGER,
    total_trips BIGINT NOT NULL,
    total_revenue NUMERIC(14, 2) NOT NULL,
    avg_fare NUMERIC(10, 2),
    avg_distance NUMERIC(10, 2),
    avg_duration NUMERIC(10, 2),
    PRIMARY KEY (pickup_year, pickup_month)
);

-- 7. Aggregate Taxi Zone Performance Table
CREATE TABLE IF NOT EXISTS agg_zone_metrics (
    location_id INTEGER PRIMARY KEY REFERENCES dim_taxi_zone(location_id),
    total_pickups BIGINT NOT NULL,
    total_revenue NUMERIC(14, 2) NOT NULL,
    avg_fare NUMERIC(10, 2),
    avg_distance NUMERIC(10, 2),
    avg_duration NUMERIC(10, 2)
);
