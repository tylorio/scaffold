import pytest
from django.test import Client
from django.urls import reverse

from analisis.models import Participante
from refuerzo.acceso import SESION_ESTUDIANTE


@pytest.fixture
def client(client, django_user_model):
    """Por defecto se prueba como investigador con sesión iniciada (8c)."""
    client.force_login(django_user_model.objects.create_user("investigador", password="x"))
    return client


@pytest.fixture
def cliente_anonimo():
    return Client()


def material(client, concepto, codigo="P01"):
    """Abre la sesión del estudiante en el cliente y devuelve la dirección de su material."""
    sesion = client.session
    sesion[SESION_ESTUDIANTE] = Participante.objects.get(codigo=codigo).pk
    sesion.save()
    return reverse("estudiante:concepto", args=[concepto])
