DOCKER_COMPOSE_DEV = docker compose -f docker-compose.dev.yaml
DOCKER_COMPOSE_BUILD = docker compose -f docker-compose.build.yaml
DOCKER_COMPOSE_DEPLOY = docker compose -f docker-compose.deploy.yaml
PYTHON = python3
UV = uv

.PHONY: help
help:
	@echo "Available commands:"
	@echo "  make dev                    - Build and start dev environment"
	@echo "  make build-registry         - Build images for artifact registry"
	@echo "  make build-dev              - Build dev Docker images"
	@echo "  make up-dev                 - Start dev containers"
	@echo "  make stop-dev               - Stop dev containers"
	@echo "  make clean-dev              - Remove dev containers and volumes"
	@echo "  make restart-dev            - Restart dev containers"
	@echo "  make logs-dev               - View dev container logs"
	@echo "  make deploy                 - Deploy to GCP (down + up)"
	@echo "  make deploy-up              - Start deployment containers"
	@echo "  make deploy-down            - Stop deployment containers"
	@echo "  make test                   - Run all tests"
	@echo "  make test-agg               - Run aggregator tests"
	@echo "  make test-scraper           - Run scraper tests"
	@echo "  make ruff-check             - Run ruff linter"
	@echo "  make ruff-format            - Run ruff formatter"
	@echo "  make ruff                   - Run both ruff check and format"

.PHONY: up-dev
up-dev:
	$(DOCKER_COMPOSE_DEV) up -d

.PHONY: build-dev
build-dev:
	$(DOCKER_COMPOSE_DEV) build

.PHONY: build-registry
build-registry:
	$(DOCKER_COMPOSE_BUILD) build

.PHONY: dev
dev: build-dev up-dev

.PHONY: deploy-up
deploy-up:
	$(DOCKER_COMPOSE_DEPLOY) up -d

.PHONY: deploy-down
deploy-down:
	$(DOCKER_COMPOSE_DEPLOY) down

.PHONY: deploy-run
deploy: deploy-down deploy-up


.PHONY: stop-dev
stop-dev:
	$(DOCKER_COMPOSE_DEV) down

.PHONY: clean-dev
clean-dev:
	$(DOCKER_COMPOSE_DEV) down -v

.PHONY: restart-dev
restart-dev: stop-dev up-dev

.PHONY: ruff-check
ruff-check:
	$(PYTHON) -m ruff check services/aggregator services/scraper

.PHONY: logs-dev
logs-dev:
	$(DOCKER_COMPOSE_DEV) logs -f

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
