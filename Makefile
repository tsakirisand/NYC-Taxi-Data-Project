.PHONY: setup download validate transform load analytics dashboard test lint docker-up docker-down clean

PYTHON = PYTHONPATH=. ./venv/bin/python
PIP = ./venv/bin/pip

setup:
	$(PYTHON) -m venv venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

download:
	$(PYTHON) -m src.ingestion.download_taxi_data --year 2025

validate:
	$(PYTHON) -m src.validation.validate_data

transform:
	$(PYTHON) -m src.transformation.transform_taxi_data

load:
	$(PYTHON) -m src.database.load_postgres

analytics:
	$(PYTHON) -m src.database.load_postgres --run-analytics

dashboard:
	PYTHONPATH=. ./venv/bin/streamlit run dashboard/app.py

test:
	PYTHONPATH=. ./venv/bin/pytest tests/ -v

lint:
	./venv/bin/flake8 src/ tests/ dashboard/ dags/ --max-line-length=120
	./venv/bin/black --check src/ tests/ dashboard/ dags/

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down -v

clean:
	rm -rf data/raw/*.parquet data/validated/*.parquet data/processed/*.parquet *.db *.log .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +
