#!/usr/bin/env bash
set -e
docker compose exec core python manage.py loaddata database/seeds/*.json