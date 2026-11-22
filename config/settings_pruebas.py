"""Configuración para pytest: no depende de un .env ni de una clave real."""
import os

from django.core.management.utils import get_random_secret_key

os.environ.setdefault("DJANGO_SECRET_KEY", get_random_secret_key())

from .settings import *  # noqa: E402,F401,F403
