from django.urls import path

from . import views

app_name = "refuerzo"

urlpatterns = [
    path("exportar/intentos.csv", views.exportar_intentos, name="exportar_intentos"),
    path("exportar/aperturas.csv", views.exportar_aperturas, name="exportar_aperturas"),
    path("<str:codigo>/<str:concepto>/", views.ver_concepto, name="concepto"),
]
