from django.urls import path

from . import views

app_name = "refuerzo"

urlpatterns = [
    path("<str:codigo>/<str:concepto>/", views.ver_concepto, name="concepto"),
]
