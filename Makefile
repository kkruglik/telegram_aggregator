DOCKER_COMPOSE_DEV = docker-compose -f docker-compose.dev.yaml
DOCKER_COMPOSE_PROD = docker-compose -f docker-compose.prod.yaml
PYTHON = python3
UV = uv

.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make dev                    - Build and start dev environment"
	@echo "  make prod                   - Build and start prod environment"
	@echo "  make build-dev              - Build dev Docker images"
	@echo "  make build-prod             - Build prod Docker images"
	@echo "  make up-dev                 - Start dev containers"
	@echo "  make up-prod                - Start prod containers"
	@echo "  make stop-dev               - Stop dev containers"
	@echo "  make stop-prod              - Stop prod containers"
	@echo "  make clean-dev              - Remove dev containers and volumes"
	@echo "  make clean-prod             - Remove prod containers and volumes"
	@echo "  make restart-dev            - Restart dev containers"
	@echo "  make restart-prod           - Restart prod containers"
	@echo "  make logs-dev               - View dev container logs"
	@echo "  make logs-prod              - View prod container logs"
	@echo "  make test                   - Run all tests"
	@echo "  make test-agg               - Run aggregator tests"
	@echo "  make test-scraper           - Run scraper tests"
	@echo "  make ruff-check             - Run ruff linter"
	@echo "  make ruff-format            - Run ruff formatter"
	@echo "  make ruff                   - Run both ruff check and format"

.PHONY: up-dev
up-dev:
	$(DOCKER_COMPOSE_DEV) up -d

.PHONY: up-prod
up-prod:
	$(DOCKER_COMPOSE_PROD) up -d


.PHONY: build-dev
build-dev:
	$(DOCKER_COMPOSE_DEV) build

.PHONY: build-prod
build-prod:
	$(DOCKER_COMPOSE_PROD) build

.PHONY: dev
dev: build-dev up-dev

.PHONY: prod
prod: build-prod up-prod

.PHONY: stop-dev
stop-dev:
	$(DOCKER_COMPOSE_DEV) down

.PHONY: stop-prod
stop-prod:
	$(DOCKER_COMPOSE_PROD) down

.PHONY: clean-dev
clean-dev:
	$(DOCKER_COMPOSE_DEV) down -v

.PHONY: clean-prod
clean-prod:
	$(DOCKER_COMPOSE_PROD) down -v

.PHONY: restart-dev
restart-dev: stop-dev up-dev

.PHONY: restart-prod
restart-prod: stop-prod up-prod

.PHONY: ruff-check
ruff-check:
	$(PYTHON) -m ruff check services/aggregator services/scraper

.PHONY: logs-dev
logs-dev:
	$(DOCKER_COMPOSE_DEV) logs -f

.PHONY: logs-prod
logs-prod:
	$(DOCKER_COMPOSE_PROD) logs -f

.PHONY: ruff-format
ruff-format:
	$(PYTHON) -m ruff format services/aggregator services/scraper

.PHONY: ruff
ruff: ruff-check ruff-format

.PHONY: test-agg
test-agg:
	$(PYTHON) -m pytest services/aggregator/tests

.PHONY: test-scraper
test-scraper:
	$(PYTHON) -m pytest services/scraper/tests

.PHONY: test
test: test-agg test-scraper