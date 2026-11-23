"""Configuración para pytest: no depende de un .env ni de una clave real."""
import os
import secrets

from django.core.management.utils import get_random_secret_key

os.environ.setdefault("DJANGO_SECRET_KEY", get_random_secret_key())
os.environ.setdefault("IDC_SAL_CORREOS", secrets.token_hex(32))
os.environ["IDC_ALMACEN"] = ""  # las pruebas nunca tocan el almacén real, montado o no

from .settings import *  # noqa: E402,F401,F403
