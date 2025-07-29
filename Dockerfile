# Use an official Python runtime as a parent image.
# We choose a specific version (3.11-slim-bullseye) for stability and smaller image size.
# 'bullseye' is Debian 11, which is actively maintained.
FROM python:3.11-slim-bullseye

# Set the working directory inside the container.
# All subsequent commands will be executed in this directory.
WORKDIR /app

# Install system dependencies required for psycopg2 (PostgreSQL adapter) and netcat.
# These are necessary to compile and run the database driver, and for wait_for_it.sh.
# - apt-get update: Updates the list of available packages.
# - apt-get install -y: Installs packages without asking for confirmation.
# - build-essential: Provides compilers and other tools needed for building software.
# - libpq-dev: Development files for PostgreSQL client library (needed by psycopg2).
# - python3-dev: Header files and static libraries for Python (needed for compiling Python extensions).
# - gcc: C compiler.
# - libc-dev: C standard library development files.
# - netcat: A networking utility used by wait_for_it.sh to check port availability.
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    python3-dev \
    gcc \
    libc-dev \
    netcat \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the working directory.
# This step is done separately to leverage Docker's layer caching.
# If only requirements.txt changes, only this layer and subsequent ones are rebuilt.
COPY requirements.txt .

# Install Python dependencies.
# - pip install --no-cache-dir: Installs packages from requirements.txt.
# - --no-cache-dir: Prevents pip from storing cache, reducing image size.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire Django project into the container's working directory.
# The '.' at the end means copy everything from the current directory on the host.
COPY . .

# Set the entrypoint for the container. This script will run first.
# All subsequent arguments from CMD or docker-compose command will be passed to it.
ENTRYPOINT ["/app/wait_for_it.sh"]

# Define the default command to run after the entrypoint.
# These arguments are passed to wait_for_it.sh.
# The -- separates wait_for_it.sh's arguments from the command it should execute.
# Only run the Django server here, as migrations/collectstatic are handled by 'make install'
CMD ["db:5432", "--", "python", "manage.py", "runserver", "0.0.0.0:8000"]

# Expose the port that Django's development server (or Gunicorn/Uvicorn in production) will listen on.
# This tells Docker that the container will listen on port 8000.
EXPOSE 8000
