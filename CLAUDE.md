a CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Structure

This is a Telegram news aggregator system built with Python 3.13+ consisting of two main microservices:

1. **Aggregator Service** (`services/aggregator/`) - Main bot service handling user interactions and content delivery
2. **Scraper Service** (`services/scraper/`) - Scrapes content from Telegram channels via Telethon

The system uses PostgreSQL for data persistence and supports both containerized (Docker) and local development.

## Development Commands

### Setup and Installation
```bash
# Install dependencies with pip (manual setup required)
# Install dependencies with uv (manual setup required)
# Note: Use manual pip/uv installation - no make targets available
```

### Running the Application
```bash
# Start full development environment with Docker
make dev

# Production deployment
make prod

# Individual container management
make build-dev      # Build dev images
make build-prod     # Build prod images
make up-dev         # Start dev containers
make up-prod        # Start prod containers
make stop-dev       # Stop dev containers
make stop-prod      # Stop prod containers
make restart-dev    # Restart dev containers
make restart-prod   # Restart prod containers
```

### Testing and Code Quality
```bash
# Run all tests
make test           # Run all tests
make test-agg       # Run aggregator tests only
make test-scraper   # Run scraper tests only

# Linting and formatting
make ruff-check     # Check code with ruff
make ruff-format    # Format code with ruff
make ruff           # Both check and format
```

### Database Operations
```bash
# Database initialization not available via make targets
# Use manual database setup procedures
```

### Container Management
```bash
# View logs
make logs-dev       # View dev container logs
make logs-prod      # View prod container logs

# Clean up containers and volumes
make clean-dev      # Remove dev containers and volumes
make clean-prod     # Remove prod containers and volumes

# Note: Container shell access not available via make targets
# Use docker exec commands directly
```

## Core Architecture

### Registry Pattern
The system implements a Registry pattern for managing entities:

- **UserRegistry** (`services/aggregator/src/app/core/registry.py:14-137`) - Manages user lifecycle, loads from database, schedules notifications
- **FeedsRegistry** (`services/aggregator/src/app/core/registry.py:139-265`) - Manages feed lifecycle, reference counting, and channel normalization

### Entity Classes
- **User** (`services/aggregator/src/app/core/user.py`) - Individual user with feeds, notifications, and subscription management
- **TelegramFeed** (`services/aggregator/src/app/core/feed.py`) - Individual feed with content scraping, summarization, and database persistence

### Key Design Patterns
- Entities handle individual state and operations
- Registries handle collection management and lifecycle
- Async/await throughout with proper error handling
- Database operations abstracted through repository pattern
- Task scheduling for user notifications via APScheduler

### Service Communication
- Aggregator calls Scraper via HTTP endpoints
- Scraper exposes REST API for channel data retrieval
- Both services connect to shared PostgreSQL database

### Database Schema
- Users table with timezone and notification preferences
- Feeds table with channel information
- Posts table with content and summaries
- Junction table for user-feed subscriptions

## Configuration

Each service has YAML configuration files in their respective `config/` directories:
- `config-local.yaml` - Local development
- `config-local-docker.yaml` - Docker development
- `config-prod.yaml` - Production

Configuration is selected via `CONFIG_NAME` environment variable.

## Testing Strategy

### Aggregator Service
- Uses pytest with asyncio support
- Hypothesis for property-based testing
- Mock objects for external dependencies
- Tests located in `services/aggregator/tests/`

### Scraper Service
- Uses pytest with coverage support
- HTTP client testing with httpx
- Unit tests for all components
- Tests located in `services/scraper/tests/unit/`

## Environment Variables

Required environment variables (create `.env` file):
```
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=postgres  # 'localhost' for local dev
DB_PORT=5432

BOT_TOKEN=your_bot_token
API_ID=your_api_id
API_HASH=your_api_hash
TELEGRAM_SESSION_NAME=your_session_name

GCP_PROJECT_ID=your_gcp_project_id
GEMINI_API_KEY=your_gemini_api_key
```

## Development Notes

- Python 3.13+ required for both aggregator and scraper services
- Uses uv for dependency management (preferred over pip)
- Ruff for linting and formatting (replacing flake8/black)
- Google Cloud integration for logging and AI summarization
- Telethon for Telegram API interactions
- aiogram for bot framework
- AsyncPG for database connectivity

## Service Dependencies

### Aggregator Dependencies
- aiogram, asyncpg, alembic, apscheduler
- google-cloud-logging, google-genai
- fastapi, uvicorn for health endpoints

### Scraper Dependencies  
- telethon for Telegram API
- fastapi, uvicorn for REST API
- google-cloud integrations