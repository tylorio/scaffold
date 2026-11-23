import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from analisis.models import Configuracion, Participante
from refuerzo.acceso import SESION_ESTUDIANTE


@pytest.fixture
def client(client, django_user_model):
    """Por defecto se prueba como investigador con sesión iniciada (8c)."""
    client.force_login(django_user_model.objects.create_user("investigador", password="x"))
    return client


@pytest.fixture
def cliente_anonimo():
    return Client()


def bloques_listos(inicio=None):
    """Carga y valida el bloque de ejemplo de cada concepto y abre la semana 1."""
    from refuerzo.administracion import cargar_bloques
    from refuerzo.models import BloqueRefuerzo
    from refuerzo.servicios.banco import bloques_de_ejemplo

    if not BloqueRefuerzo.objects.exists():
        cargar_bloques(bloques_de_ejemplo(), "pruebas")
        BloqueRefuerzo.objects.update(validado=True, n_jueces=3)
    configuracion = Configuracion.obtener()
    if configuracion.inicio_intervencion is None:
        configuracion.inicio_intervencion = inicio or timezone.localdate()
        configuracion.save()


def material(client, concepto, codigo="P01"):
    """Abre la sesión del estudiante y devuelve la dirección del bloque de ejemplo."""
    bloques_listos()
    sesion = client.session
    sesion[SESION_ESTUDIANTE] = Participante.objects.get(codigo=codigo).pk
    sesion.save()
    return reverse("estudiante:bloque", args=[concepto, f"{concepto}-ejemplo"])
