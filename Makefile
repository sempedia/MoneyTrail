# Makefile for MoneyTrail Transaction Tracker

# Define variables for common commands and service names
DOCKER_COMPOSE = docker compose
DJANGO_MANAGE = python manage.py
WEB_SERVICE = web
DB_SERVICE = db
APP_NAME = MoneyTrail # Your Django app name

# Dynamically get the Docker Compose project name.
# Docker Compose typically uses the current current directory's basename as the project name.
# `basename "$$PWD"` gets the current directory name (e.g., 'MoneyTrail_Project').
# `tr '[:upper:]' '[:lower:]'` converts it to lowercase, matching Docker Compose's default.
PROJECT_NAME := $(shell basename "$$PWD" | tr '[:upper:]' '[:lower:]')

.PHONY: all build up start down down-volumes install migrate makemigrations superuser fetchdata test clean

# Default target when 'make' is run without arguments
all: up

# Build all Docker images defined in docker-compose.yml
build:
	@echo "Building Docker images..."
	$(DOCKER_COMPOSE) build

# Start Docker containers in detached mode (-d)
up:
	@echo "Starting Docker containers..."
	$(DOCKER_COMPOSE) up -d

# Start Docker containers in foreground mode (for initial setup/debugging)
start:
	@echo "Starting Docker containers in foreground..."
	$(DOCKER_COMPOSE) up

# Stop Docker containers
down:
	@echo "Stopping Docker containers..."
	$(DOCKER_COMPOSE) down

# Stop Docker containers and remove volumes (clears database data)
down-volumes:
	@echo "Stopping Docker containers and removing volumes (database data will be lost)..."
	$(DOCKER_COMPOSE) down -v

# Initial setup: build images, run migrations, and static files collection...
# This is a convenient target for first-time setup.
# Note: For 'docker compose run', we explicitly set the entrypoint to 'sh'
# and use '-c' to run the Django management commands as a single string.
install: build
	@echo "Running initial setup: migrations and static files collection..."
	$(DOCKER_COMPOSE) run --rm --entrypoint sh $(WEB_SERVICE) -c "$(DJANGO_MANAGE) makemigrations $(APP_NAME)" # <--- CHANGE HERE
	$(DOCKER_COMPOSE) run --rm --entrypoint sh $(WEB_SERVICE) -c "$(DJANGO_MANAGE) migrate" # <--- CHANGE HERE
	$(DOCKER_COMPOSE) run --rm --entrypoint sh $(WEB_SERVICE) -c "$(DJANGO_MANAGE) collectstatic --noinput" # <--- CHANGE HERE
	$(DOCKER_COMPOSE) up -d

# Run Django database migrations
migrate:
	@echo "Running Django database migrations..."
	$(DOCKER_COMPOSE) exec $(WEB_SERVICE) $(DJANGO_MANAGE) migrate

# Create Django migration files for the MoneyTrail app
makemigrations:
	@echo "Creating Django migration files for $(APP_NAME) app..."
	$(DOCKER_COMPOSE) exec $(WEB_SERVICE) $(DJANGO_MANAGE) makemigrations $(APP_NAME)

# Create a Django superuser
superuser:
	@echo "Creating Django superuser..."
	$(DOCKER_COMPOSE) exec $(WEB_SERVICE) $(DJANGO_MANAGE) createsuperuser

# Fetch dummy transaction data using the custom management command
fetchdata:
	@echo "Fetching dummy transaction data..."
	$(DOCKER_COMPOSE) exec $(WEB_SERVICE) $(DJANGO_MANAGE) fetch_transactions

# Run automated tests for the MoneyTrail app
test:
	@echo "Running automated tests..."
	$(DOCKER_COMPOSE) exec $(WEB_SERVICE) $(DJANGO_MANAGE) test $(APP_NAME)

# Clean up Docker resources SPECIFIC TO THIS PROJECT
# This target aims to remove only the containers, volumes, and images directly
# associated with the current Docker Compose project, leaving other Docker
# resources (from other projects) untouched.
clean: down-volumes
	@echo "Removing Docker images specific to MoneyTrail Project..."
	@# Attempt to remove the Docker image built for the 'web' service of this project.
	@# The image name is typically formed by combining the project name and service name (e.g., 'moneytrail_project_web').
	@# The '-' prefix before 'docker rmi' tells Make to ignore any errors (e.g., if the image doesn't exist).
	@# '|| true' ensures that even if 'docker rmi' fails, the shell command itself exits successfully,
	@# preventing Make from stopping the entire clean process.
	-docker rmi $(PROJECT_NAME)_$(WEB_SERVICE) || true
	@echo "Cleanup complete for MoneyTrail Project."
