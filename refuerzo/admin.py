from django.contrib import admin

from .models import AperturaRefuerzo, BloqueRefuerzo, IntentoEjercicio

admin.site.register(AperturaRefuerzo)
admin.site.register(IntentoEjercicio)


@admin.register(BloqueRefuerzo)
class BloqueRefuerzoAdmin(admin.ModelAdmin):
    """Solo lectura: los bloques se cargan con cargar_bloques y se validan en Gestión."""

    list_display = ("id", "concepto", "semana", "orden", "version", "validado")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
