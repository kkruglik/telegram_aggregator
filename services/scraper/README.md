# Telegram Scraper

A microservice for scraping Telegram channels and retrieving messages.

## Features

- Retrieve messages from Telegram channels by ID or name
- Get channel ID from channel username or link
- Health check endpoint
- Configurable via YAML files
- Google Cloud Logging integration

## Setup

1. Clone the repository
2. Create a configuration file in the `config` directory (see `config-local.yaml` for an example)
3. Set the `CONFIG_NAME` environment variable to the name of your configuration file
4. Install dependencies:
   ```bash
   pip install -e .
   ```

## Running the Service

```bash
# Set the configuration file
export CONFIG_NAME=config-local.yaml

# Run the service
python -m src.app.main
```

Or using uvicorn directly:

```bash
export CONFIG_NAME=config-local.yaml
uvicorn src.app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

- `POST /messages_by_id`: Get messages from a channel by ID
- `POST /messages_by_name`: Get messages from a channel by name
- `POST /channel_id`: Get a channel ID from a username or link
- `GET /health`: Health check endpoint

## Testing

The project includes comprehensive unit tests for all components. To run the tests:

1. Install test dependencies:
   ```bash
   pip install -e ".[test]"
   ```

2. Run the tests:
   ```bash
   pytest
   ```

3. Run tests with coverage:
   ```bash
   pytest --cov=src
   ```

4. Run specific test files:
   ```bash
   pytest tests/unit/app/test_models.py
   ```

5. Run tests with verbose output:
   ```bash
   pytest -v
   ```

## Docker

The service can be run in a Docker container:

```bash
# Build the image
docker build -t telegram-scraper .

# Run the container
docker run -p 8000:8000 -e CONFIG_NAME=config-local-docker.yaml telegram-scraper
```
