-- NYC Taxi Data Engineering - Database Indexes

-- Indexes on Fact Trips for query optimization
CREATE INDEX IF NOT EXISTS idx_fact_trips_pickup_datetime ON fact_trips(tpep_pickup_datetime);
CREATE INDEX IF NOT EXISTS idx_fact_trips_pickup_date ON fact_trips(pickup_date);
CREATE INDEX IF NOT EXISTS idx_fact_trips_pulocation ON fact_trips(pulocation_id);
CREATE INDEX IF NOT EXISTS idx_fact_trips_dolocation ON fact_trips(dolocation_id);
CREATE INDEX IF NOT EXISTS idx_fact_trips_payment_type ON fact_trips(payment_type);
CREATE INDEX IF NOT EXISTS idx_fact_trips_pickup_hour ON fact_trips(pickup_hour);

-- Composite Indexes
CREATE INDEX IF NOT EXISTS idx_fact_trips_zone_date ON fact_trips(pulocation_id, pickup_date);
CREATE INDEX IF NOT EXISTS idx_fact_trips_route ON fact_trips(pulocation_id, dolocation_id);
