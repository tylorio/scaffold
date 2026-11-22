from django.http import HttpResponse


def respuesta_csv(contenido, nombre):
    respuesta = HttpResponse(contenido, content_type="text/csv; charset=utf-8")
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
    return respuesta
