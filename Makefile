# Makefile for Weather Data Analysis Pipeline

.PHONY: help install dev-install test lint format clean docker-build docker-run

help:
	@echo "Available commands:"
	@echo "  install      Install the package and dependencies"
	@echo "  dev-install  Install with development dependencies"
	@echo "  test         Run the test suite"
	@echo "  lint         Run linting checks"
	@echo "  format       Format code with black and isort"
	@echo "  clean        Clean up build artifacts"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run with Docker Compose"

install:
	pip install -r requirements.txt
	pip install -e .

dev-install:
	pip install -r requirements.txt
	pip install -e .[dev]

test:
	pytest tests/ -v --cov=src/weather_pipeline

lint:
	flake8 src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/

format:
	black src/ tests/
	isort src/ tests/

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

docker-build:
	docker build -t weather-pipeline .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

# Development commands
dev-run-dashboard:
	python -m src.weather_pipeline.cli dashboard

dev-collect-data:
	python -m src.weather_pipeline.cli collect

dev-stats:
	python -m src.weather_pipeline.cli stats

dev-test-connections:
	python -m src.weather_pipeline.cli test all