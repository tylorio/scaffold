from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cuenta/entrar/', auth.LoginView.as_view(template_name='cuenta/entrar.html'), name='entrar'),
    path('cuenta/salir/', auth.LogoutView.as_view(), name='salir'),
    path('gestion/', include('analisis.urls_gestion')),
    path('refuerzo/', include('refuerzo.urls')),
    path('', include('refuerzo.urls_estudiante')),
]

# Las vistas del investigador sobre análisis y código existen solo en local (ADR-001).
if settings.LOCAL:
    urlpatterns.append(path('', include('analisis.urls')))
else:
    urlpatterns.append(path('', RedirectView.as_view(pattern_name='estudiante:acceso')))
