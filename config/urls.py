from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('refuerzo/', include('refuerzo.urls')),
]

# Las vistas del investigador sobre análisis y código existen solo en local (ADR-001).
if settings.LOCAL:
    urlpatterns.append(path('', include('analisis.urls')))
