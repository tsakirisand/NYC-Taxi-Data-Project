# 🚕 NYC Taxi Data Engineering Pipeline

An end-to-end, enterprise-grade Data Engineering project processing the official **NYC TLC Yellow Taxi Trip Record Data (2025)** using **PySpark**, **PostgreSQL**, **Apache Airflow**, **Streamlit**, and **Docker**.

Designed as a high-impact portfolio project demonstrating distributed data processing, automated validation, relational database modeling, advanced analytical SQL, dynamic dashboarding, and cloud-ready modular architecture.

---

## 🏗️ Architecture Overview

```mermaid
flowchart TD
    subgraph Data Source & Ingestion
        A[NYC TLC CloudFront\nYellow Taxi Parquet 2025] -->|src/ingestion/download_taxi_data.py| B[(Raw Data Lake\ndata/raw/*.parquet)]
        Ref[Taxi Zone Lookup CSV] -->|Reference Data| RefFolder[(data/reference/)]
    end

    subgraph Data Quality & Validation Engine
        B -->|src/validation/validate_data.py| C{Quality Assurances\nNulls, Ranges, Duplicates}
        C -->|Valid Records| D[(Validated Parquet\ndata/validated/)]
        C -->|Log Metrics & Bad Records| M[Validation JSON Logs]
    end

    subgraph Distributed PySpark Transformations
        D -->|src/transformation/transform_taxi_data.py| E[PySpark Distributed Session]
        E -->|Feature Engineering & Aggregations| F[(Processed Parquet\ndata/processed/)]
    end

    subgraph Relational Warehouse & Analytics
        F -->|src/database/load_postgres.py| G[(PostgreSQL Warehouse\nfact_trips & dim tables)]
        G -->|sql/analytics.sql| H[Analytical SQL Engine\nCTEs & Window Functions]
        G -->|dashboard/app.py| I[Interactive Streamlit Dashboard\nPlotly Analytics UI]
    end

    subgraph Orchestration & Infrastructure
        J[Apache Airflow DAG\ndags/taxi_pipeline.py] -. Orchestrates Tasks .-> A
        J -. Orchestrates .-> C
        J -. Orchestrates .-> E
        J -. Orchestrates .-> G
        Docker[Docker Compose\nPostgres, Airflow, Streamlit] -. Hosts Services .-> G
    end
```

---

## 🛠️ Technology Stack

| Domain | Technology | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.12+ | Core development & pipeline execution |
| **Distributed Compute** | Apache Spark (PySpark) | Large-scale feature engineering & aggregations |
| **Data Format** | Apache Parquet & PyArrow | High-performance columnar file storage |
| **Relational Database** | PostgreSQL / SQLite | Data warehousing & analytical queries |
| **Data Validation** | PyArrow & Pydantic | Data quality assertions & metric logging |
| **Orchestration** | Apache Airflow | Pipeline DAG scheduling & task dependencies |
| **Dashboard & UI** | Streamlit & Plotly | Interactive analytics dashboard & visualizations |
| **Containerization** | Docker & Docker Compose | Containerized multi-service deployment |
| **Testing & CI/CD** | Pytest, Flake8, Black, GitHub Actions | Automated linting, verification, and CI/CD |

---

## 📊 Data Source

This pipeline processes the official NYC Taxi & Limousine Commission (TLC) Yellow Taxi trip records:
- **Source URL**: `https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page`
- **Data Format**: Parquet columnar files for 2025 (`yellow_tripdata_2025-01.parquet`, etc.)
- **API Key**: No API key required. Direct CloudFront download.

---

## 🔍 Data Validation Rules & Quality Assurances

The validation engine (`src/validation/validate_data.py`) enforces the following data-quality assertions before allowing records into PySpark:
1. **Null Timestamps Check**: Rejects records with missing pickup or dropoff datetimes.
2. **Invalid Duration Check**: Rejects trips where dropoff is before pickup or total duration exceeds 24 hours (`duration_minutes > 1440`).
3. **Distance Check**: Rejects trips with `trip_distance <= 0`.
4. **Fare Check**: Rejects negative fares (`fare_amount < 0` or `total_amount < 0`).
5. **Passenger Count**: Filters invalid passenger counts (`passenger_count <= 0` or `passenger_count > 9`).
6. **Spatial Location IDs**: Validates `PULocationID` and `DOLocationID` are within valid NYC TLC range (`1..265`).
7. **Exact Deduplication**: Drops duplicate trip records.
8. **Threshold Assertion**: Fails gracefully if overall row rejection ratio exceeds 50%.

---

## ⚡ PySpark Transformations

The distributed transformation engine (`src/transformation/transform_taxi_data.py`) calculates key derived fields:
- **`trip_duration_minutes`**: Precise duration in minutes.
- **`avg_speed_mph`**: Calculated trip velocity.
- **`tip_percentage`**: `(tip_amount / fare_amount) * 100`.
- **`pickup_date`, `pickup_hour`, `pickup_day_of_week`**: Temporal feature extractions.
- **`is_peak_hour`**: Boolean flag for NYC weekday rush hours (07:00-09:00 & 16:00-19:00).
- **Aggregations**: Computes distributed summaries for hourly, daily, monthly, and zone performance metrics.

---

## 🗄️ Relational Data Warehouse Schema

```text
                  +-------------------+
                  |   dim_taxi_zone   |
                  +-------------------+
                  | location_id (PK)  |
                  | borough           |
                  | zone              |
                  | service_zone      |
                  +---------+---------+
                            |
                            | 1:N
                            v
+------------------+      +-------------------+
|     dim_date     |      |    fact_trips     |
+------------------+      +-------------------+
| date_key (PK)    |<----+| trip_id (PK)      |
| year             | 1:N  | pulocation_id(FK) |
| month            |      | dolocation_id(FK) |
| day              |      | pickup_datetime   |
| day_name         |      | dropoff_datetime  |
| is_weekend       |      | trip_distance     |
+------------------+      | fare_amount       |
                          | total_amount      |
                          | tip_percentage    |
                          | avg_speed_mph     |
                          +-------------------+
```

---

## 📈 Analytical SQL Queries (`sql/analytics.sql`)

The project includes 13 advanced SQL queries using **CTEs** and **Window Functions**:
1. **Most Popular Month**: Identifies peak trip volume months.
2. **Top Revenue Month**: Computes highest grossing monthly period.
3. **Busiest Hours**: Evaluates hourly demand distribution with window percentages (`SUM OVER ()`).
4. **Day-of-Week Volume**: Aggregates demand patterns across weekdays vs weekends.
5. **Top Pickup Zones**: Ranks busiest pickup locations via `DENSE_RANK() OVER`.
6. **Most Profitable Zones**: Ranks zones by total revenue and average fare per trip.
7. **Distance & Speed Breakdown**: Compares peak vs off-peak average speeds.
8. **Payment Method Analysis**: Aggregates fare and tip metrics across credit card, cash, and dispute payments.
9. **Tip Propensity**: Calculates overall percentage of tipped trips and average tip rates.
10. **Trip Duration Statistics**: Evaluates min, max, and average trip lengths.
11. **Month-over-Month (MoM) Revenue Growth**: Uses `LAG(revenue, 1) OVER (ORDER BY month)` to measure revenue velocity.
12. **Top 10 Origin-Destination Routes**: Ranks busiest zone pairs.
13. **Airport Trip Intelligence**: Categorizes JFK, Newark, and LaGuardia trips via zone & rate code lookups.

---

## 🖥️ Streamlit Interactive Dashboard

Launch the interactive dashboard to visualize metrics and explore taxi demand:

```bash
make dashboard
# Or directly:
streamlit run dashboard/app.py
```

### Features:
- **KPI Metrics**: Total Trips, Revenue, Avg Fare, Avg Distance, Avg Duration, Avg Tip %.
- **Plotly Visualizations**: Hourly demand heatmaps, day-of-week trends, top pickup zone rankings, and distribution histograms.
- **Dynamic Filters**: Multi-select filtering by Month, Pickup Zone, and Payment Type.

---

## 🚀 Quickstart & Local Setup

### Prerequisites
- Python 3.12+
- Java 17 (Required for PySpark)
- Docker & Docker Compose (Optional for containerized mode)

### 1. Clone Repository & Install Dependencies
```bash
git clone https://github.com/your-username/nyc-taxi-data-engineering.git
cd nyc-taxi-data-engineering

# Set up Python virtual environment and dependencies
make setup
```

### 2. Copy Environment Template
```bash
cp .env.example .env
```

### 3. Run Pipeline End-to-End Locally
```bash
# Download 2025 Month 1 Yellow Taxi data
make download

# Validate raw data quality
make validate

# Execute PySpark transformation job
make transform

# Load transformed datasets into relational database
make load

# Run analytical SQL queries
make analytics
```

### 4. Run Pytest Test Suite
```bash
make test
```

---

## 🐳 Running with Docker & Docker Compose

To start PostgreSQL, Apache Airflow, and Streamlit in containerized environment:

```bash
# Build and start services in background
make docker-up

# Service URLs:
# - Streamlit Dashboard: http://localhost:8501
# - Airflow Web UI:     http://localhost:8080
# - PostgreSQL:          localhost:5432
```

---

## ☁️ Future AWS Cloud Scalability Architecture

To scale this pipeline to enterprise cloud volumes, the architecture is designed for seamless AWS Lakehouse migration:

```mermaid
flowchart LR
    A[NYC TLC Stream] -->|AWS Kinesis / MSK| B[Spark Streaming]
    B -->|Raw Parquet| C[(AWS S3 Raw Bucket)]
    C -->|AWS Glue PySpark Job| D[(AWS S3 Processed Iceberg Lake)]
    D -->|Glue Catalog| E[AWS Athena Serverless SQL]
    E -->|Connector| F[QuickSight / Streamlit Dashboard]
    Airflow[AWS MWAA / Airflow] -. Orchestrates .-> D
```

### Scalability Migration Plan:
1. **Object Storage**: Swap local `data/raw` and `data/processed` paths with `s3://nyc-taxi-data-lake/`. The `StorageManager` module natively supports S3 URIs.
2. **Serverless Distributed ETL**: Migrate `transform_taxi_data.py` to an **AWS Glue PySpark** job triggered via Amazon EventBridge or Apache Airflow on **AWS MWAA**.
3. **Serverless SQL Engine**: Register processed Iceberg / Parquet tables in **AWS Glue Data Catalog** and query with **AWS Athena**.
4. **Real-time Streaming**: Replace batch monthly downloads with **Amazon MSK (Managed Streaming for Kafka)** and **Spark Structured Streaming** for real-time surge pricing analytics.

---

## 📜 License & Acknowledgments

- **Data Credit**: NYC TLC (Taxi & Limousine Commission) for public trip records.
- **License**: MIT License.
