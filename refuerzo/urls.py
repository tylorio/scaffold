from django.urls import path

from . import views

app_name = "refuerzo"

urlpatterns = [
    path("exportar/intentos.csv", views.exportar_intentos, name="exportar_intentos"),
    path("exportar/aperturas.csv", views.exportar_aperturas, name="exportar_aperturas"),
    path("exportar/adherencia.csv", views.exportar_adherencia, name="exportar_adherencia"),
]
