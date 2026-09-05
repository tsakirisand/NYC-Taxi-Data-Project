-- NYC Taxi Data Engineering - Analytical SQL Queries
-- ANSI SQL & PostgreSQL Standard Syntax

-- Query 1: Which month had the most trips?
WITH MonthlyTrips AS (
    SELECT 
        pickup_year AS trip_year,
        pickup_month AS trip_month,
        COUNT(*) AS total_trips,
        RANK() OVER (ORDER BY COUNT(*) DESC) AS trip_rank
    FROM fact_trips
    GROUP BY pickup_year, pickup_month
)
SELECT trip_year, trip_month, total_trips
FROM MonthlyTrips
WHERE trip_rank = 1;


-- Query 2: Which month generated the most revenue?
WITH MonthlyRevenue AS (
    SELECT 
        pickup_year AS trip_year,
        pickup_month AS trip_month,
        ROUND(SUM(total_amount), 2) AS total_revenue,
        RANK() OVER (ORDER BY SUM(total_amount) DESC) AS revenue_rank
    FROM fact_trips
    GROUP BY pickup_year, pickup_month
)
SELECT trip_year, trip_month, total_revenue
FROM MonthlyRevenue
WHERE revenue_rank = 1;


-- Query 3: What are the busiest pickup hours?
WITH HourlyVolume AS (
    SELECT 
        pickup_hour,
        COUNT(*) AS trip_count,
        SUM(COUNT(*)) OVER () AS grand_total_trips
    FROM fact_trips
    GROUP BY pickup_hour
)
SELECT 
    pickup_hour,
    trip_count,
    ROUND((trip_count * 100.0 / grand_total_trips), 2) AS percent_of_total_trips,
    RANK() OVER (ORDER BY trip_count DESC) AS hour_rank
FROM HourlyVolume
ORDER BY hour_rank;


-- Query 4: What are the busiest days of the week?
SELECT 
    pickup_day_of_week,
    COUNT(*) AS total_trips,
    ROUND(SUM(total_amount), 2) AS total_revenue,
    ROUND(AVG(fare_amount), 2) AS avg_fare
FROM fact_trips
GROUP BY pickup_day_of_week
ORDER BY total_trips DESC;


-- Query 5: What are the top pickup taxi zones?
SELECT 
    z.location_id,
    z.borough,
    z.zone,
    COUNT(f.trip_id) AS total_pickups,
    DENSE_RANK() OVER (ORDER BY COUNT(f.trip_id) DESC) AS pickup_rank
FROM fact_trips f
JOIN dim_taxi_zone z ON f.pulocation_id = z.location_id
GROUP BY z.location_id, z.borough, z.zone
ORDER BY pickup_rank
LIMIT 10;


-- Query 6: What are the most profitable taxi zones?
SELECT 
    z.location_id,
    z.borough,
    z.zone,
    COUNT(f.trip_id) AS total_trips,
    ROUND(SUM(f.total_amount), 2) AS total_revenue,
    ROUND(AVG(f.total_amount), 2) AS avg_revenue_per_trip,
    RANK() OVER (ORDER BY SUM(f.total_amount) DESC) AS revenue_rank
FROM fact_trips f
JOIN dim_taxi_zone z ON f.pulocation_id = z.location_id
GROUP BY z.location_id, z.borough, z.zone
ORDER BY total_revenue DESC
LIMIT 10;


-- Query 7: What is the average trip distance overall and by peak vs non-peak?
SELECT 
    is_peak_hour,
    COUNT(*) AS total_trips,
    ROUND(AVG(trip_distance), 2) AS avg_trip_distance,
    ROUND(AVG(avg_speed_mph), 2) AS avg_speed_mph
FROM fact_trips
GROUP BY is_peak_hour;


-- Query 8: What is the average fare by payment type?
SELECT 
    payment_type,
    CASE payment_type
        WHEN 1 THEN 'Credit Card'
        WHEN 2 THEN 'Cash'
        WHEN 3 THEN 'No Charge'
        WHEN 4 THEN 'Dispute'
        ELSE 'Unknown'
    END AS payment_type_desc,
    COUNT(*) AS total_trips,
    ROUND(AVG(fare_amount), 2) AS avg_fare_amount,
    ROUND(AVG(total_amount), 2) AS avg_total_amount,
    ROUND(AVG(tip_amount), 2) AS avg_tip_amount
FROM fact_trips
GROUP BY payment_type
ORDER BY total_trips DESC;


-- Query 9: What percentage of trips include tips?
WITH TipStats AS (
    SELECT 
        COUNT(*) AS total_trips,
        SUM(CASE WHEN tip_amount > 0 THEN 1 ELSE 0 END) AS trips_with_tip,
        ROUND(AVG(tip_percentage), 2) AS avg_tip_pct_overall,
        ROUND(AVG(CASE WHEN tip_amount > 0 THEN tip_percentage ELSE NULL END), 2) AS avg_tip_pct_when_tipped
    FROM fact_trips
)
SELECT 
    total_trips,
    trips_with_tip,
    ROUND((trips_with_tip * 100.0 / total_trips), 2) AS percent_trips_tipped,
    avg_tip_pct_overall,
    avg_tip_pct_when_tipped
FROM TipStats;


-- Query 10: What is the average trip duration?
SELECT 
    ROUND(AVG(trip_duration_minutes), 2) AS avg_duration_minutes,
    ROUND(MIN(trip_duration_minutes), 2) AS min_duration_minutes,
    ROUND(MAX(trip_duration_minutes), 2) AS max_duration_minutes
FROM fact_trips;


-- Query 11: How does revenue change month over month?
WITH MonthlySummary AS (
    SELECT 
        pickup_year AS trip_year,
        pickup_month AS trip_month,
        ROUND(SUM(total_amount), 2) AS current_month_revenue
    FROM fact_trips
    GROUP BY pickup_year, pickup_month
),
MoMCalculation AS (
    SELECT 
        trip_year,
        trip_month,
        current_month_revenue,
        LAG(current_month_revenue, 1) OVER (ORDER BY trip_year, trip_month) AS prev_month_revenue
    FROM MonthlySummary
)
SELECT 
    trip_year,
    trip_month,
    current_month_revenue,
    prev_month_revenue,
    ROUND(current_month_revenue - prev_month_revenue, 2) AS mom_revenue_change,
    ROUND(((current_month_revenue - prev_month_revenue) * 100.0 / NULLIF(prev_month_revenue, 0)), 2) AS mom_growth_pct
FROM MoMCalculation
ORDER BY trip_year, trip_month;


-- Query 12: What are the top 10 routes (Pickup Zone to Dropoff Zone)?
WITH RouteStats AS (
    SELECT 
        pz.zone AS pickup_zone,
        dz.zone AS dropoff_zone,
        COUNT(*) AS route_trip_count,
        ROUND(AVG(f.fare_amount), 2) AS avg_route_fare,
        ROUND(AVG(f.trip_distance), 2) AS avg_route_distance
    FROM fact_trips f
    JOIN dim_taxi_zone pz ON f.pulocation_id = pz.location_id
    JOIN dim_taxi_zone dz ON f.dolocation_id = dz.location_id
    GROUP BY pz.zone, dz.zone
)
SELECT 
    pickup_zone,
    dropoff_zone,
    route_trip_count,
    avg_route_fare,
    avg_route_distance,
    DENSE_RANK() OVER (ORDER BY route_trip_count DESC) AS route_rank
FROM RouteStats
ORDER BY route_rank
LIMIT 10;


-- Query 13: What are the busiest airport-related trips?
SELECT 
    CASE 
        WHEN f.rate_code_id = 2 OR pz.zone LIKE '%Airport%' OR dz.zone LIKE '%Airport%' THEN 'JFK Airport'
        WHEN f.rate_code_id = 3 OR pz.zone LIKE '%Newark%' OR dz.zone LIKE '%Newark%' THEN 'Newark Airport'
        WHEN f.rate_code_id = 4 OR pz.zone LIKE '%LaGuardia%' OR dz.zone LIKE '%LaGuardia%' THEN 'Nassau/LaGuardia'
        ELSE 'Standard City Trip'
    END AS airport_category,
    COUNT(*) AS total_trips,
    ROUND(SUM(f.total_amount), 2) AS total_revenue,
    ROUND(AVG(f.fare_amount), 2) AS avg_fare,
    ROUND(AVG(f.airport_fee), 2) AS avg_airport_fee
FROM fact_trips f
JOIN dim_taxi_zone pz ON f.pulocation_id = pz.location_id
JOIN dim_taxi_zone dz ON f.dolocation_id = dz.location_id
GROUP BY 1
ORDER BY total_trips DESC;
