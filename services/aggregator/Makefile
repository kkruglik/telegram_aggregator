# Makefile for Telegram Aggregator Project

# Variables
DOCKER_COMPOSE_DEV = docker-compose -f docker-compose.dev.yaml
DOCKER_COMPOSE_PROD = docker-compose -f docker-compose.prod.yaml
PYTHON = python3
PIP = pip3
UV = uv

# Default target
.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make setup              - Install dependencies with pip"
	@echo "  make setup-uv           - Install dependencies with uv"
	@echo "  make dev                - Start development environment with Docker"
	@echo "  make dev-local          - Start development environment locally without Docker"
	@echo "  make prod               - Start production environment"
	@echo "  make build              - Build Docker images"
	@echo "  make stop               - Stop all containers"
	@echo "  make clean              - Remove all containers and volumes"
	@echo "  make test               - Run tests"
	@echo "  make init-db            - Initialize database in Docker"
	@echo "  make init-local-db      - Initialize local database"
	@echo "  make logs               - View logs"
	@echo "  make lint               - Run linting"
	@echo "  make format             - Format code"
	@echo "  make ruff-check         - Run ruff linter"
	@echo "  make ruff-format        - Run ruff formatter"
	@echo "  make ruff               - Run both ruff check and format"
	@echo "  make run-local-aggregator - Run aggregator locally"
	@echo "  make run-local-scraper  - Run scraper locally"

# Setup development environment
.PHONY: setup
setup:
	$(PIP) install -e .
	$(PIP) install -e ".[dev]"

# Setup development environment with uv
.PHONY: setup-uv
setup-uv:
	$(UV) pip install -e .
	$(UV) pip install -e ".[dev]"

# Start development environment
.PHONY: dev
dev:
	$(DOCKER_COMPOSE_DEV) up -d

# Start development environment locally without Docker
.PHONY: dev-local
dev-local: run-local-scraper run-local-aggregator

# Start production environment
.PHONY: prod
prod:
	$(DOCKER_COMPOSE_PROD) up -d

# Build Docker images
.PHONY: build
build:
	$(DOCKER_COMPOSE_DEV) build
	$(DOCKER_COMPOSE_PROD) build

# Stop all containers
.PHONY: stop
stop:
	$(DOCKER_COMPOSE_DEV) down
	$(DOCKER_COMPOSE_PROD) down

# Remove all containers and volumes
.PHONY: clean
clean:
	$(DOCKER_COMPOSE_DEV) down -v
	$(DOCKER_COMPOSE_PROD) down -v
	rm -rf logs/*.log

# Run tests
.PHONY: test
test:
	$(PYTHON) -m pytest tests/

# Initialize database
.PHONY: init-db
init-db:
	$(DOCKER_COMPOSE_DEV) exec postgres psql -U $${DB_USER} -d $${DB_NAME} -f /app/init_db.sql

# Initialize local database
.PHONY: init-local-db
init-local-db:
	psql -U $${DB_USER} -d $${DB_NAME} -f init_db.sql

# View logs
.PHONY: logs
logs:
	$(DOCKER_COMPOSE_DEV) logs -f

# Run linting
.PHONY: lint
lint:
	$(PYTHON) -m flake8 tg_aggregator_src tg_scraper_src tests

# Format code
.PHONY: format
format:
	$(PYTHON) -m black tg_aggregator_src tg_scraper_src tests

# Run ruff linter
.PHONY: ruff-check
ruff-check:
	$(PYTHON) -m ruff check services/aggregator services/scraper

# Run ruff formatter
.PHONY: ruff-format
ruff-format:
	$(PYTHON) -m ruff format services/aggregator services/scraper

# Run both ruff check and format
.PHONY: ruff
ruff: ruff-check ruff-format

# Restart services
.PHONY: restart
restart:
	$(DOCKER_COMPOSE_DEV) restart

# Show running containers
.PHONY: ps
ps:
	$(DOCKER_COMPOSE_DEV) ps

# Enter shell in container
.PHONY: shell-aggregator
shell-aggregator:
	$(DOCKER_COMPOSE_DEV) exec aggregator bash

.PHONY: shell-scraper
shell-scraper:
	$(DOCKER_COMPOSE_DEV) exec scraper bash

.PHONY: shell-db
shell-db:
	$(DOCKER_COMPOSE_DEV) exec postgres bash

# Run components locally
.PHONY: run-local-aggregator
run-local-aggregator:
	cd tg_aggregator_src && $(PYTHON) -m tg_aggregator.main

.PHONY: run-local-scraper
run-local-scraper:
	cd tg_scraper_src && $(PYTHON) -m app.main
