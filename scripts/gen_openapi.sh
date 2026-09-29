#!/usr/bin/env bash
set -e
cd backend/api
python -c "import main; main.app.openapi()" > ../../frontend/openapi.json