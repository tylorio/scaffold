from django.urls import path

from . import gestion

app_name = "gestion"

urlpatterns = [
    path("", gestion.panel, name="panel"),
    path(
        "participantes/<str:codigo>/codigo-acceso/", gestion.codigo_acceso,
        name="codigo_acceso",
    ),
    path("importar/", gestion.importar, name="importar"),
]
