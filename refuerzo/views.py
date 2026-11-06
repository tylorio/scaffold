from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from analisis.models import Participante
from analisis.servicios.conceptos import NOMBRES_CONCEPTOS

from .models import IntentoEjercicio
from .servicios.contenido import generar_recurso
from .servicios.ejecutor import ejecutar_solucion, usa_concepto

MAXIMO_CARACTERES = 20_000


def _ejercicios_con_intento(recurso, analisis):
    intentos = analisis.intentos.filter(concepto=recurso.concepto)
    ultimos = {}
    for intento in intentos:  # vienen del más nuevo al más antiguo
        ultimos.setdefault(intento.ejercicio, intento)
    return [
        {"datos": ejercicio, "intento": ultimos.get(ejercicio.id)}
        for ejercicio in recurso.ejercicios
    ]


def ver_concepto(request, codigo, concepto):
    if concepto not in NOMBRES_CONCEPTOS:
        raise Http404("Concepto desconocido")
    participante = get_object_or_404(Participante, codigo=codigo)
    analisis = participante.ultimo_analisis
    resultado = analisis.conceptos.filter(concepto=concepto).first() if analisis else None

    # El concepto de control no debe recibir material: abrirlo a mano por URL
    # contaminaría la comparación intrasujeto.
    if resultado is None or not resultado.reforzado:
        return render(
            request, "refuerzo/no_disponible.html",
            {"participante": participante, "nombre": NOMBRES_CONCEPTOS[concepto]},
            status=403,
        )

    recurso = generar_recurso(
        concepto,
        n_fragmentos=resultado.n_fragmentos,
        n_ia=resultado.n_ia,
        idc=resultado.idc,
    )

    if request.method == "POST":
        ejercicio = recurso.ejercicio(request.POST.get("ejercicio", ""))
        if ejercicio is None:
            raise Http404("Ejercicio desconocido")
        codigo_solucion = request.POST.get("codigo", "")[:MAXIMO_CARACTERES]
        ejecucion = ejecutar_solucion(
            codigo_solucion, ejercicio, settings.TIEMPO_LIMITE_EJERCICIO
        )
        IntentoEjercicio.objects.create(
            analisis=analisis,
            concepto=concepto,
            ejercicio=ejercicio.id,
            codigo=codigo_solucion,
            pasados=ejecucion.pasados,
            total=ejecucion.total,
            error=ejecucion.error,
            casos=ejecucion.casos,
            usa_concepto=usa_concepto(codigo_solucion, concepto),
        )
        url = reverse("refuerzo:concepto", args=[codigo, concepto])
        return redirect(f"{url}#{ejercicio.id}")

    return render(request, "refuerzo/concepto.html", {
        "participante": participante,
        "recurso": recurso,
        "ejercicios": _ejercicios_con_intento(recurso, analisis),
    })
