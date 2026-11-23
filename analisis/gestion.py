"""Gestión del investigador en los dos perfiles: códigos de acceso e importación.

No importa nada que traiga Git ni el modelo: también corre en la nube.
"""
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from refuerzo.acceso import generar_codigo_acceso

from .models import Congelacion, Importacion, Participante
from .resultados import ArchivoInvalido, importar_resultados

MAXIMO_ARCHIVO = 5 * 1024 * 1024


@login_required
def panel(request):
    return render(request, "analisis/gestion.html", {
        "participantes": Participante.objects.select_related("asignacion").order_by("codigo"),
        "congelacion": Congelacion.objects.first(),
        "importaciones": Importacion.objects.all()[:10],
        "importar": not settings.LOCAL,
    })


@never_cache
@login_required
@require_POST
def codigo_acceso(request, codigo):
    participante = get_object_or_404(Participante, codigo=codigo)
    nuevo = generar_codigo_acceso(participante, request.user.get_username())
    return render(request, "analisis/codigo_acceso.html", {
        "participante": participante, "codigo_acceso": nuevo,
    })


@login_required
@require_POST
def importar(request):
    if settings.LOCAL:
        raise Http404("La importación solo existe en el portal.")
    archivo = request.FILES.get("archivo")
    if archivo is None or archivo.size > MAXIMO_ARCHIVO:
        messages.error(request, "Sube un archivo resultados-v1 de menos de 5 MB.")
        return redirect("gestion:panel")
    try:
        texto = archivo.read().decode("utf-8")
        importacion, nuevos = importar_resultados(texto, request.user.get_username())
    except UnicodeDecodeError:
        messages.error(request, "El archivo no está en UTF-8.")
    except ArchivoInvalido as error:
        messages.error(request, f"Archivo rechazado: {error}")
    else:
        messages.success(
            request,
            f"Importación {importacion.pk}: {nuevos} participantes nuevos de "
            f"{importacion.n_participantes}.",
        )
    return redirect("gestion:panel")
