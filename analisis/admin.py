from django.contrib import admin

from .models import Analisis, Asignacion, Configuracion, Participante

admin.site.register(Configuracion)
admin.site.register(Participante)
admin.site.register(Analisis)


@admin.register(Asignacion)
class AsignacionAdmin(admin.ModelAdmin):
    """Se puede borrar para repetir a un participante, pero no editar: es un sorteo."""

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
