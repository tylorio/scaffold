from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('refuerzo/', include('refuerzo.urls')),
    path('', include('analisis.urls')),
]
