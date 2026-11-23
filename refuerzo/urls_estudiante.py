"""Rutas del estudiante: ninguna lleva su código; el participante sale de la sesión."""
from django.urls import path

from . import views

app_name = "estudiante"

urlpatterns = [
    path("acceso/", views.acceso, name="acceso"),
    path("salir/", views.salir, name="salir"),
    path("mi/", views.inicio, name="inicio"),
    path("mi/informe/", views.informe, name="informe"),
    path("mi/refuerzo/<str:concepto>/", views.ver_concepto, name="concepto"),
    path("mi/refuerzo/<str:concepto>/<str:bloque_id>/", views.ver_bloque, name="bloque"),
]
