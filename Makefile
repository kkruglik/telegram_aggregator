DOCKER_COMPOSE_DEV = docker compose -f docker-compose.dev.yaml
DOCKER_COMPOSE_BUILD = docker compose -f docker-compose.build.yaml
DOCKER_COMPOSE_DEPLOY = docker compose -f docker-compose.deploy.yaml
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
	@echo "  make sync                   - Install dependencies"
	@echo "  make run-local              - Run bot locally"
	@echo "  make test                   - Run tests"
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

.PHONY: logs-dev
logs-dev:
	$(DOCKER_COMPOSE_DEV) logs -f

.PHONY: sync
sync:
	$(UV) sync

.PHONY: run-local
run-local:
	$(UV) run python -m src.app.main

.PHONY: ruff-check
ruff-check:
	$(UV) run ruff check src

.PHONY: ruff-format
ruff-format:
	$(UV) run ruff format src

.PHONY: ruff
ruff: ruff-check ruff-format

.PHONY: test
test:
	$(UV) run pytest tests
