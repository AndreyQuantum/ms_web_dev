.PHONY: help up down logs build test test-products test-orders migrate-products migrate-orders lint clean

SHELL := /bin/bash
PYTHON ?= python
COMPOSE ?= docker compose

help:
	@echo "Targets:"
	@echo "  up                 Start the full stack (docker compose up -d)"
	@echo "  down               Stop and remove all containers"
	@echo "  logs               Tail compose logs"
	@echo "  build              Build all service images"
	@echo "  test               Run tests for both services"
	@echo "  test-products      Run products tests"
	@echo "  test-orders        Run orders tests"
	@echo "  migrate-products   Run alembic upgrade head for products"
	@echo "  migrate-orders     Run alembic upgrade head for orders"
	@echo "  lint               Run ruff over both services"
	@echo "  clean              Remove caches and stopped containers"

up:
	$(COMPOSE) up -d

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=200

build:
	$(COMPOSE) build

test: test-products test-orders

test-products:
	cd products_microservice && $(PYTHON) -m pytest -v

test-orders:
	cd orders_microservice && $(PYTHON) -m pytest -v

migrate-products:
	cd products_microservice && alembic upgrade head

migrate-orders:
	cd orders_microservice && alembic upgrade head

lint:
	cd products_microservice && ruff check . && ruff format --check .
	cd orders_microservice && ruff check . && ruff format --check .

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .ruff_cache -exec rm -rf {} + 2>/dev/null || true
	$(COMPOSE) down --remove-orphans 2>/dev/null || true
