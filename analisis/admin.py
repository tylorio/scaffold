from django.contrib import admin

from .models import Analisis, Configuracion, Participante

admin.site.register(Configuracion)
admin.site.register(Participante)
admin.site.register(Analisis)
