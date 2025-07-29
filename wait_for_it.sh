#!/bin/sh
# wait-for-it.sh: Waits for a host:port to be available.

# Usage: ./wait-for-it.sh host:port [-- command args]
# Example: ./wait-for-it.sh db:5432 -- python manage.py migrate

TIMEOUT=15  # How long to wait in seconds
QUIET=0     # Set to 1 for quiet mode

# Function to print messages
log() {
  if [ "$QUIET" -ne 1 ]; then
    echo "$@"
  fi
}

# Parse arguments
HOSTPORT=$1
shift

# Check if host:port is provided
if [ -z "$HOSTPORT" ]; then
  log "Error: Host and port not provided."
  log "Usage: $0 host:port [-- command args]"
  exit 1
fi

# Split host and port
HOST=$(echo "$HOSTPORT" | cut -d: -f1)
PORT=$(echo "$HOSTPORT" | cut -d: -f2)

# Check if port is numeric
if ! [ "$PORT" -eq "$PORT" ] 2>/dev/null; then
  log "Error: Port must be a number."
  log "Usage: $0 host:port [-- command args]"
  exit 1
fi

log "Waiting for $HOST:$PORT to be ready..."

start_time=$(date +%s)
while ! nc -z "$HOST" "$PORT"; do
  current_time=$(date +%s)
  elapsed_time=$((current_time - start_time))
  if [ "$elapsed_time" -ge "$TIMEOUT" ]; then
    log "Error: Timeout after $TIMEOUT seconds waiting for $HOST:$PORT."
    exit 1
  fi
  sleep 1
done

log "$HOST:$PORT is ready!"

# Execute the command if provided
if [ "$#" -gt 0 ]; then
  # Remove '--' separator if present
  if [ "$1" = "--" ]; then
    shift
  fi
  exec "$@"
fi
