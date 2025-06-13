#!/bin/sh
set -e

# Start the backend in the background
uvicorn app.main:app --host 0.0.0.0 --port 8000 &

# Start nginx in the foreground
exec nginx -g 'daemon off;'
