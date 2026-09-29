#!/usr/bin/env bash
set -e
cd /app/backend/core
exec celery -A config.celery worker -l info