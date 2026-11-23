from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ConfiguracionForm, ParticipanteForm
from .http import respuesta_csv
from .models import Configuracion, Participante
from .persistencia import (
    AsignacionCongelada,
    NoSePuedeCongelar,
    RepositorioSinFunciones,
    SinCorreosDeclarados,
    congelacion,
    congelar_asignacion,
    ejecutar_analisis,
    estado_congelacion,
    exportar_csv,
    exportar_csv_analisis,
)
from .servicios.clasificador import ModeloNoDisponible
from .servicios.conceptos import NOMBRES_CONCEPTOS
from .servicios.repositorio import ErrorRepositorio, OrigenInvalido


def _usuario(request) -> str:
    return request.user.get_username() or "web"


@login_required
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
        "estado": estado_congelacion(),
    })


@login_required
@require_POST
def analizar(request, codigo):
    participante = get_object_or_404(Participante, codigo=codigo)
    reemplaza = participante.ultimo_analisis is not None
    try:
        analisis = ejecutar_analisis(participante, usuario=_usuario(request))
    except (
        OrigenInvalido, ErrorRepositorio, ModeloNoDisponible, RepositorioSinFunciones,
        SinCorreosDeclarados, AsignacionCongelada,
    ) as error:
        messages.error(request, str(error))
        return redirect("analisis:lista")
    messages.success(
        request,
        f"Diagnóstico completado: {analisis.n_fragmentos} fragmentos."
        + (" Reemplaza al análisis anterior." if reemplaza else ""),
    )
    if analisis.archivos_con_error:
        messages.warning(
            request,
            "Archivos omitidos porque no se pudieron leer: "
            + ", ".join(analisis.archivos_con_error),
        )
    return redirect("analisis:detalle", codigo=codigo)


@login_required
def detalle_participante(request, codigo):
    participante = get_object_or_404(Participante, codigo=codigo)
    analisis = participante.ultimo_analisis
    contexto = {
        "participante": participante,
        "analisis": analisis,
        "asignacion": getattr(participante, "asignacion", None),
        "congelada": congelacion() is not None,
    }
    if analisis is not None:
        conceptos = list(analisis.conceptos.all())
        contexto.update({
            "conceptos": conceptos,
            "debiles": [c for c in conceptos if c.estado == "debil"],
            "fragmentos": analisis.fragmentos.all(),
        })
    return render(request, "analisis/detalle.html", contexto)


@login_required
def configuracion(request):
    config = Configuracion.obtener()
    form = ConfiguracionForm(
        request.POST or None, instance=config, congelada=congelacion() is not None,
    )
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


@login_required
def congelar(request):
    """Muestra qué va a pasar y, al confirmar, congela la asignación de todos (D3)."""
    if request.method == "POST":
        try:
            hecha = congelar_asignacion(usuario=_usuario(request))
        except (NoSePuedeCongelar, AsignacionCongelada) as error:
            messages.error(request, str(error))
            return redirect("analisis:congelar")
        messages.success(
            request,
            f"Asignación congelada el {hecha.fecha:%d/%m/%Y %H:%M}, en modo {hecha.modo}. "
            "Ya no se puede reanalizar a nadie.",
        )
        return redirect("analisis:lista")
    return render(request, "analisis/congelar.html", {"estado": estado_congelacion()})


@login_required
def exportar(request):
    return respuesta_csv(exportar_csv(), "participantes_idc.csv")


@login_required
def exportar_analisis(request):
    return respuesta_csv(exportar_csv_analisis(), "analisis_idc.csv")
