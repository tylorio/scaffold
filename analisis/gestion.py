"""Gestión del investigador en los dos perfiles: códigos de acceso, importación e
intervención (inicio, bloques validados y liberación del control tras el postest).

No importa nada que traiga Git ni el modelo: también corre en la nube.
"""
from datetime import date

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from refuerzo.acceso import ParticipanteRetirado, generar_codigo_acceso
from refuerzo.administracion import (
    AccionNoPermitida,
    fijar_inicio,
    liberar_control,
    validar_bloque,
)
from refuerzo.liberacion import intervencion
from refuerzo.models import BloqueRefuerzo
from refuerzo.servicios.banco import ranuras_faltantes

from .models import Configuracion, Congelacion, Importacion, Participante
from .participacion import CambioNoPermitido, carpeta_a_borrar, retirar
from .servicios.conceptos import NOMBRES_CONCEPTOS
from .resultados import ArchivoInvalido, importar_resultados

MAXIMO_ARCHIVO = 5 * 1024 * 1024


@login_required
def panel(request):
    bloques = list(BloqueRefuerzo.objects.all())
    faltantes = ranuras_faltantes([(b.concepto, b.semana, b.orden) for b in bloques])
    return render(request, "analisis/gestion.html", {
        "participantes": Participante.objects.select_related("asignacion").order_by("codigo"),
        "congelacion": Congelacion.objects.first(),
        "importaciones": Importacion.objects.all()[:10],
        "importar": not settings.LOCAL,
        "configuracion": Configuracion.obtener(),
        "intervencion": intervencion(),
        "bloques": bloques,
        "faltantes": [
            {"nombre": NOMBRES_CONCEPTOS[c], "ranuras": r} for c, r in faltantes.items() if r
        ],
    })


def _usuario(request):
    return request.user.get_username()


def _accion(request, funcion, *args, exito):
    try:
        funcion(*args, _usuario(request))
    except AccionNoPermitida as error:
        messages.error(request, str(error))
    else:
        messages.success(request, exito)
    return redirect("gestion:panel")


@login_required
@require_POST
def inicio_intervencion(request):
    try:
        fecha = date.fromisoformat(request.POST.get("fecha", ""))
    except ValueError:
        messages.error(request, "Indica una fecha válida.")
        return redirect("gestion:panel")
    return _accion(
        request, fijar_inicio, fecha,
        exito=f"La intervención empieza el {fecha:%d/%m/%Y}.",
    )


@login_required
@require_POST
def liberar(request):
    if request.POST.get("confirmo") != "si":
        messages.error(request, "Confirma que todos los participantes ya rindieron el postest.")
        return redirect("gestion:panel")
    return _accion(
        request, liberar_control,
        exito="Material liberado: cada participante ve ahora los tres conceptos.",
    )


@login_required
@require_POST
def validar(request, bloque_id):
    try:
        version = int(request.POST.get("version", ""))
        n_jueces = int(request.POST.get("n_jueces", ""))
    except ValueError:
        messages.error(request, "Indica la versión y el número de jueces.")
        return redirect("gestion:panel")
    return _accion(
        request, validar_bloque, bloque_id, version, n_jueces,
        exito=f"{bloque_id} v{version} validado.",
    )


@never_cache
@login_required
@require_POST
def codigo_acceso(request, codigo):
    participante = get_object_or_404(Participante, codigo=codigo)
    try:
        nuevo = generar_codigo_acceso(participante, _usuario(request))
    except ParticipanteRetirado as error:
        messages.error(request, str(error))
        return redirect("gestion:panel")
    return render(request, "analisis/codigo_acceso.html", {
        "participante": participante, "codigo_acceso": nuevo,
    })


@login_required
@require_POST
def retiro(request, codigo):
    participante = get_object_or_404(Participante, codigo=codigo)
    if request.POST.get("confirmo", "").strip() != codigo:
        messages.error(request, f"Para borrar los datos de {codigo}, escribe su código.")
        return redirect("gestion:panel")
    carpeta = carpeta_a_borrar(participante.repositorio)
    try:
        retirar(participante, _usuario(request))
    except CambioNoPermitido as error:
        messages.error(request, str(error))
    else:
        otro = "el portal" if settings.LOCAL else "el núcleo local"
        messages.success(
            request, f"Datos de {codigo} borrados. Haz el mismo retiro en {otro}.",
        )
        if carpeta:
            messages.warning(
                request, f"Borra también la carpeta que entregó: {carpeta}",
            )
    return redirect("gestion:panel")


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
        importacion, nuevos = importar_resultados(texto, _usuario(request))
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
