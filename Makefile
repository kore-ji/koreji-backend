SHELL := /bin/bash

# Default target: build and start services (migrations run automatically on startup)
all: up

# Build the Docker images using docker-compose
build:
	@echo "Building docker images..."
	docker compose build

# Start services in background
up:
	@echo "Starting services..."
	docker compose up -d --build

# Stop services (keeps data)
stop:
	@echo "Stopping services..."
	docker compose stop

# Stop and remove containers (keeps volumes/data)
down:
	@echo "Stopping and removing containers..."
	docker compose down

# Stop and remove containers, networks AND volumes (destroys all data)
clean:
	@echo "Stopping services and removing all data..."
	docker compose down -v

# Manually run migrations (usually not needed as entrypoint handles this)
migrate:
	@echo "Running alembic migrations..."
	docker compose run --rm koreji-backend alembic upgrade head

# Tail logs for all services
logs:
	docker compose logs -f

# Show recent logs
logs-tail:
	docker compose logs --tail=100

.PHONY: all build up stop down clean migrate logs logs-tail shell ps