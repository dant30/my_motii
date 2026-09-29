"""Celery application for Django domain tasks."""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("my_motii")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()