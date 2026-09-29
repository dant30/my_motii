"""Local development settings."""

from .base import *  # noqa: F403

DEBUG = env_bool("DJANGO_DEBUG", True)  # noqa: F405
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"