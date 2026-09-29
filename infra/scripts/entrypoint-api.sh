#!/usr/bin/env bash
set -e
cd /app/backend/api
exec uvicorn main:app --host 0.0.0.0 --port 8001 --reload