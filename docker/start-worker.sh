#!/bin/bash
set -e

echo "Starting Xvfb..."
Xvfb :99 -screen 0 1920x1080x24 -ac &
sleep 2

echo "Xvfb started on display :99"
export DISPLAY=:99

# Verify Xvfb is running
if ! xdpyinfo -display :99 >/dev/null 2>&1; then
    echo "Warning: Xvfb may not be fully initialized, but continuing..."
fi

echo "Starting Celery worker..."
exec celery -A backend.worker worker \
    --loglevel=info \
    --concurrency=2 \
    --pool=prefork \
    -Q celery,video_generation,default
