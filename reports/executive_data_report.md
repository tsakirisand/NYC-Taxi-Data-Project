# 📊 Executive Analytics & Data Engineering Report: NYC Yellow Taxi (2025)

## 1. 📈 Empirical Data Summary

| Category | Metric Name | Value | Empirical Insight |
| :--- | :--- | :--- | :--- |
| **Macro Metrics** | Total Validated Trips | **3,253,069** | Jan 2025 single-month dataset after validation |
| | Total Gross Revenue | **$88,099,745.77** | **$88.10M** gross revenue generated |
| | Total Driver Tips | **$10,153,637.67** | Represents ~11.5% of total gross revenue |
| **Trip Economics** | Average Fare | **$18.22** | Base fare + distance charges |
| | Average Distance | **5.51 miles** | Short intra-city travel dominates |
| | Average Duration | **15.13 minutes** | Standard commute window |
| | Average Tip % | **19.94%** | Average tip percentage across all trips |
| **Peak Hours** | Busiest Pickup Hour | **6:00 PM (18:00)** | **236,509 trips** ($6.21M revenue) |
| | Top Revenue Hour | **5:00 PM (17:00)** | **$6,319,395.81 gross revenue** |
| | Slowest Night Hour | **4:00 AM (04:00)** | **17,936 trips** ($551K revenue) |
| **Day of Week** | Busiest Day | **Thursday** | **571,720 trips** ($15.58M revenue) |
| | Second Busiest Day | **Friday** | **544,084 trips** ($14.72M revenue) |
| | Slowest Day | **Monday** | **343,539 trips** ($10.53M revenue) |
| **Taxi Zones** | Top Volume Pickup | **Midtown Center** | **161,338 trips** ($3.86M revenue) |
| | Highest Grossing Zone | **JFK Airport** | **$10,914,272.71 revenue** ($62.64 avg fare) |
| **Payment Dynamics**| Credit Card Share | **74.5% (2.42M trips)** | **94.3% tip rate** (26.29% avg tip) |
| | Cash Share | **11.3% (368K trips)** | 0% recorded digital tips |

---

## 2. 🔍 Analytical Insights

1. **Thursday Evening Peak Demand**: Thursday generates **571,720 trips** ($15.58M revenue), outperforming Monday by **66.4%**. Post-pandemic hybrid office schedules concentrate in-person office presence and after-work dining/events on Thursdays.
2. **JFK Airport Revenue Magnet**: While Midtown Center leads in total trip volume (161k), JFK Airport generates **2.8x more revenue ($10.91M vs $3.86M)** at an average fare of **$62.64 per trip** due to regulated flat rates and long trip distances.
3. **POS Screen Tipping Nudge**: Passengers paying via Credit Card tip on **94.3% of trips** at an average of **26.29%**, driven by default tip prompt screens on modern payment terminals.
4. **Rush Hour Speed Penalty**: During evening rush hours (3:00 PM - 6:00 PM), average vehicle velocity drops to **12.8 - 18.5 mph** compared to **26.5 mph late at night**.

---

## 3. 🛠️ Data Engineering & ETL Pipeline Quality Audit

| Pipeline Stage | Metric / Rule | Value | Description & Technical Impact |
| :--- | :--- | :--- | :--- |
| **Raw Ingestion** | Total Input Records | **3,475,226** | Initial raw parquet file size downloaded from NYC TLC |
| **Validation Gate**| Clean Validated Rows | **3,253,069** | **93.61% pass rate** retained for analytical warehouse |
| | Rejected Outliers | **222,157 (6.39%)** | Filtered by automated `DataValidator` quality checks |
| **Quality Audit** | Negative Fares / Refunds | **144,439 rows** | Cancelled/disputed trips filtered from revenue calculations |
| | Zero / Negative Distance | **90,893 rows** | Stationary or aborted trips removed from velocity models |
| | Out-of-Range Duration | **2,092 rows** | Trips > 24 hours removed as taximeter sensor errors |
| | Clock Calibration Errors| **21 rows** | Out-of-year taximeter records (e.g. 2024-12-31) filtered |
| **Warehouse** | Partitioning Strategy | `pickup_date` | Clustered indexing on `pulocation_id` & `pickup_hour` |

---

## 4. 🗽 Borough & Regional Spatial Dynamics

- **Manhattan Core Dominance**: Accounts for **89.2% of all pickups** (2.90M trips). High-density commercial corridors (Midtown, Upper East Side, Times Square) generate consistent short-haul demand.
- **Airport Hub Efficiency**: JFK and LaGuardia Airports account for **8.4% of total trips** but **18.7% of total revenue**. Airport trips average **13.8 miles** compared to the citywide average of **5.51 miles**.
- **Outer Borough Coverage**: Brooklyn, Bronx, and Staten Island represent < 3% of Yellow Taxi pickups, highlighting market division between Yellow Taxis (Manhattan core) and FHV/Uber (outer boroughs).

---

## 5. 🏁 Strategic Policy & Operational Recommendations

1. **Fleet Staging & Driver Dispatch**: Stage drivers in Midtown Manhattan on **Thursday/Friday afternoons (3 PM - 8 PM)** and maintain dedicated airport queues at **JFK Airport** where fares average 3.4x higher than Manhattan local trips.
2. **Dynamic Surge & Congestion Management**: Leverage real-time velocity metrics to optimize congestion pricing surcharges during the 4:00 PM - 7:00 PM commuter peak.
3. **Automated ETL Monitoring**: Maintain strict automated validation assertions (`WHERE pickup_year = 2025`) in PySpark and PostgreSQL to prevent corrupted source records from impacting executive reporting dashboards.
