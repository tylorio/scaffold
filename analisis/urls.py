from django.urls import path

from . import views

app_name = "analisis"

urlpatterns = [
    path("", views.lista_participantes, name="lista"),
    path("participantes/<str:codigo>/", views.detalle_participante, name="detalle"),
    path("participantes/<str:codigo>/analizar/", views.analizar, name="analizar"),
    path("configuracion/", views.configuracion, name="configuracion"),
    path("exportar.csv", views.exportar, name="exportar"),
]
