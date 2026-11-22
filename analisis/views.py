from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ConfiguracionForm, ParticipanteForm
from .models import Configuracion, Participante
from .persistencia import (
    RepositorioSinFunciones,
    SinCorreosDeclarados,
    ejecutar_analisis,
    exportar_csv,
    exportar_csv_analisis,
)
from .servicios.clasificador import ModeloNoDisponible
from .servicios.conceptos import NOMBRES_CONCEPTOS
from .servicios.repositorio import ErrorRepositorio, OrigenInvalido


def lista_participantes(request):
    form = ParticipanteForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        participante = form.save()
        messages.success(request, f"Participante {participante.codigo} registrado.")
        return redirect("analisis:lista")
    return render(request, "analisis/lista.html", {
        "participantes": (
            Participante.objects.select_related("asignacion")
            .prefetch_related("analisis")
        ),
        "form": form,
    })


@require_POST
def analizar(request, codigo):
    participante = get_object_or_404(Participante, codigo=codigo)
    try:
        analisis = ejecutar_analisis(participante)
    except (
        OrigenInvalido, ErrorRepositorio, ModeloNoDisponible, RepositorioSinFunciones,
        SinCorreosDeclarados,
    ) as error:
        messages.error(request, str(error))
        return redirect("analisis:lista")
    messages.success(
        request,
        f"Análisis {analisis.fase} completado: {analisis.n_fragmentos} fragmentos.",
    )
    if analisis.archivos_con_error:
        messages.warning(
            request,
            "Archivos omitidos porque no se pudieron leer: "
            + ", ".join(analisis.archivos_con_error),
        )
    return redirect("analisis:detalle", codigo=codigo)


def detalle_participante(request, codigo):
    participante = get_object_or_404(Participante, codigo=codigo)
    analisis = participante.ultimo_analisis
    contexto = {
        "participante": participante,
        "analisis": analisis,
        "asignacion": getattr(participante, "asignacion", None),
    }
    if analisis is not None:
        conceptos = list(analisis.conceptos.all())
        contexto.update({
            "conceptos": conceptos,
            "debiles": [c for c in conceptos if c.estado == "debil"],
            "reforzados": [c for c in conceptos if c.reforzado],
            "no_reforzados": [c for c in conceptos if not c.reforzado],
            "fragmentos": analisis.fragmentos.all(),
        })
    return render(request, "analisis/detalle.html", contexto)


def configuracion(request):
    config = Configuracion.obtener()
    form = ConfiguracionForm(request.POST or None, instance=config)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(
            request, "Configuración guardada. Se aplicará en el próximo análisis."
        )
        return redirect("analisis:configuracion")
    return render(request, "analisis/configuracion.html", {
        "form": form,
        "conceptos": NOMBRES_CONCEPTOS.values(),
    })


def respuesta_csv(contenido, nombre):
    respuesta = HttpResponse(contenido, content_type="text/csv; charset=utf-8")
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre}"'
    return respuesta


def exportar(request):
    return respuesta_csv(exportar_csv(), "participantes_idc.csv")


def exportar_analisis(request):
    return respuesta_csv(exportar_csv_analisis(), "analisis_idc.csv")
