# 📊 Executive Analytics & Data Engineering Report: NYC Yellow Taxi (2025)

## 1. 📈 Empirical Data Summary

| Category | Metric Name | Value | Empirical Insight |
| :--- | :--- | :--- | :--- |
| **Macro Metrics** | Total Validated Trips | **3,253,091** | Jan 2025 single-month dataset after validation |
| | Total Gross Revenue | **$88,100,357.07** | **$88.10M** gross revenue generated |
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

1. **Thursday Evening Peak Demand**: Thursday generates **571,720 trips** ($15.58M revenue), outperforming Monday by **66.4%**. Post-pandemic office schedules concentrate in-person office work and after-work outings on Thursdays.
2. **JFK Airport Revenue Magnet**: While Midtown Center leads in total trips (161k), JFK Airport generates **3.5x more revenue ($10.91M vs $3.86M)** at an average fare of **$62.64 per trip** due to regulated flat rates.
3. **POS Screen Tipping Nudge**: Passengers paying via Credit Card tip on **94.3% of trips** at an average of **26.29%**, driven by default tip prompts on payment terminals.
4. **Rush Hour Speed Penalty**: During evening rush hours (3:00 PM - 6:00 PM), vehicle speed drops to **12.8 - 18.5 mph** compared to **26.5 mph off-peak**.

---

## 3. 🏁 Strategic Recommendations

1. **Fleet Staging**: Stage drivers in Midtown Manhattan on **Thursday/Friday afternoons (3 PM - 8 PM)** and maintain dedicated airport queues at **JFK Airport** where fares are 4x higher than city trips.
2. **Congestion & Surge Optimization**: Leverage velocity metrics to optimize surge pricing during the 4:00 PM - 7:00 PM commuter window.
3. **Data Quality Assertions**: Maintain strict validation checks (`WHERE pickup_year = 2025`) in PySpark and PostgreSQL to filter corrupted source records.
