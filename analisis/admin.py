from django.contrib import admin

from .models import (
    Analisis,
    Asignacion,
    Auditoria,
    Configuracion,
    Congelacion,
    Importacion,
    Participante,
)

admin.site.register(Configuracion)
admin.site.register(Participante)
admin.site.register(Analisis)


class SoloLectura(admin.ModelAdmin):
    """Es un sorteo congelado: se puede consultar, no crear, editar ni borrar (D3)."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Asignacion, SoloLectura)
admin.site.register(Congelacion, SoloLectura)
admin.site.register(Auditoria, SoloLectura)
admin.site.register(Importacion, SoloLectura)
