# Telegram Aggregator

A Telegram bot that aggregates content from various Telegram channels and provides a personalized feed to users.

## Project Overview

This project consists of two main components:
- **Telegram Aggregator**: The main service that handles user interactions and content delivery
- **Telegram Scraper**: A service that scrapes content from Telegram channels

## Prerequisites

- Docker and Docker Compose (for containerized development)
- Python 3.11 or higher
- PostgreSQL (for local development without Docker)
- uv (optional, for local development with uv as package manager)

## Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Database
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=postgres  # Use 'postgres' for Docker, 'localhost' for local development
DB_PORT=5432

# Telegram
BOT_TOKEN=your_bot_token
API_ID=your_api_id
API_HASH=your_api_hash
TELEGRAM_SESSION_NAME=your_session_name

# Google Cloud
GCP_PROJECT_ID=your_gcp_project_id
GEMINI_API_KEY=your_gemini_api_key
```

> **Note:** For local development without Docker, set `DB_HOST=localhost`

## Using the Makefile

This project includes a Makefile to simplify common operations. Here are the available commands:

### Setup and Installation

```bash
# Install dependencies with pip
make setup

# Or install dependencies with uv
make setup-uv
```

### Running the Application

```bash
# Start development environment with Docker
make dev

# Start development environment locally without Docker
make dev-local

# Run aggregator component locally
make run-local-aggregator

# Run scraper component locally
make run-local-scraper

# Start production environment
make prod

# Build Docker images
make build

# Stop all containers
make stop

# Remove all containers and volumes
make clean
```

### Database Operations

```bash
# Initialize database in Docker
make init-db

# Initialize local database
make init-local-db
```

### Development Tools

```bash
# Run tests
make test

# View logs
make logs

# Run linting
make lint

# Format code
make format

# Restart services
make restart

# Show running containers
make ps
```

### Container Shells

```bash
# Enter shell in aggregator container
make shell-aggregator

# Enter shell in scraper container
make shell-scraper

# Enter shell in database container
make shell-db
```

## Project Structure

```
telegram_aggregator/
├── config/                  # Configuration files
├── logs/                    # Log files
├── tests/                   # Test files
├── tg_aggregator_src/       # Aggregator service source code
│   ├── tg_aggregator/       # Main package
│   │   ├── bot/             # Telegram bot code
│   │   ├── core/            # Core business logic
│   │   ├── db/              # Database models and repository
│   │   ├── services/        # Various services
│   │   └── utils/           # Utility functions
│   └── Dockerfile           # Dockerfile for aggregator service
├── tg_scraper_src/          # Scraper service source code
│   ├── app/                 # Scraper application
│   └── Dockerfile           # Dockerfile for scraper service
├── docker-compose.dev.yaml  # Docker Compose for development
├── docker-compose.prod.yaml # Docker Compose for production
├── init_db.sql              # Database initialization script
├── Makefile                 # Project Makefile
├── pyproject.toml           # Python project configuration
└── readme.md                # This file
```

## Development

### Running Tests

```bash
make test
```

### Code Style

This project uses Black for code formatting and Flake8 for linting:

```bash
# Format code
make format

# Run linting
make lint
```

## Local Development

You can run the application locally without Docker using the following steps:

1. Install dependencies:
   ```bash
   # Using pip
   make setup

   # Or using uv
   make setup-uv
   ```

2. Set up a local PostgreSQL database and update your `.env` file:
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=your_db_name
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   ```

3. Initialize the database:
   ```bash
   make init-local-db
   ```

4. Run the application components:
   ```bash
   # Run both components
   make dev-local

   # Or run them separately
   make run-local-scraper
   make run-local-aggregator
   ```

## Deployment

For production deployment:

```bash
make prod
```

This will start all services in production mode using the configuration in `docker-compose.prod.yaml`.

## License

[MIT License](LICENSE)
