import hashlib

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from analisis.http import respuesta_csv
from analisis.servicios.conceptos import NOMBRES_CONCEPTOS
from analisis.servicios.idc import ANCHO_INTERPRETABLE, ETIQUETAS_ESTADO, intervalo_wilson

from .acceso import (
    SESION_ESTUDIANTE,
    AccesoBloqueado,
    estudiante_requerido,
    verificar,
)
from .ejecucion import ejecutor_configurado
from .liberacion import (
    bloque_liberado,
    bloques_liberados,
    concepto_abierto,
    intervencion,
    registrar_bloqueo,
)
from .models import AperturaRefuerzo, BloqueRefuerzo, IntentoEjercicio
from .persistencia import (
    exportar_csv_adherencia,
    exportar_csv_aperturas,
    exportar_csv_intentos,
)
from .servicios.banco import introduccion
from .servicios.ejecutor import NO_DISPONIBLE, ejecutar_solucion, usa_concepto

MAXIMO_CARACTERES = 20_000


# Acceso del estudiante

def acceso(request):
    error, estado = "", 200
    if request.method == "POST":
        try:
            participante = verificar(
                request.POST.get("participante", ""), request.POST.get("codigo", ""),
                request.META.get("REMOTE_ADDR", ""),
            )
        except AccesoBloqueado:
            participante = None
            error, estado = (
                "Demasiados intentos fallidos. Espera 15 minutos antes de volver a intentarlo.",
                429,
            )
        else:
            if participante is None:
                error, estado = "El código de participante o el de acceso no son correctos.", 200
        if participante is not None:
            request.session.cycle_key()  # una sesión nueva al entrar
            request.session[SESION_ESTUDIANTE] = participante.pk
            return redirect("estudiante:inicio")
    return render(request, "refuerzo/acceso.html", {"error": error}, status=estado)


@require_POST
def salir(request):
    request.session.pop(SESION_ESTUDIANTE, None)
    return redirect("estudiante:acceso")


@estudiante_requerido
def inicio(request, participante):
    """Los conceptos que trabaja el estudiante. Sin IDC durante la intervención (D11)."""
    asignacion = getattr(participante, "asignacion", None)
    analisis = participante.ultimo_analisis
    estado = intervencion()
    conceptos = []
    if analisis is not None and (asignacion is not None or estado.liberado):
        for resultado in analisis.conceptos.all():
            abierto = concepto_abierto(participante, resultado.concepto, estado)
            conceptos.append({
                "concepto": resultado.concepto,
                "nombre": NOMBRES_CONCEPTOS[resultado.concepto],
                "abierto": abierto,
                "n_bloques": (
                    bloques_liberados(resultado.concepto, estado).count() if abierto else 0
                ),
            })
    return render(request, "refuerzo/mi.html", {
        "participante": participante, "conceptos": conceptos, "estado": estado,
    })


# Material de refuerzo

def _bloqueado(request, participante, concepto, motivo, bloque=None):
    registrar_bloqueo(participante, concepto, motivo, bloque)
    return render(
        request, "refuerzo/no_disponible.html",
        {"nombre": NOMBRES_CONCEPTOS[concepto], "motivo": motivo, "estado": intervencion()},
        status=403,
    )


@estudiante_requerido
def ver_concepto(request, participante, concepto):
    """Los bloques liberados de un concepto."""
    if concepto not in NOMBRES_CONCEPTOS:
        raise Http404("Concepto desconocido")
    estado = intervencion()
    # El concepto de control no debe recibir material: abrirlo a mano por URL
    # contaminaría la comparación intrasujeto. El intento queda registrado.
    if not concepto_abierto(participante, concepto, estado):
        return _bloqueado(request, participante, concepto, AperturaRefuerzo.CONCEPTO_BLOQUEADO)
    return render(request, "refuerzo/concepto.html", {
        "nombre": NOMBRES_CONCEPTOS[concepto],
        "concepto": concepto,
        "introduccion": introduccion(concepto),
        "bloques": bloques_liberados(concepto, estado),
        "estado": estado,
    })


def _ultimos_intentos(participante, bloque):
    intentos = IntentoEjercicio.objects.filter(
        analisis__participante=participante, bloque_id=bloque.id,
    )
    ultimos = {}
    for intento in intentos:  # vienen del más nuevo al más antiguo
        ultimos.setdefault(intento.ejercicio, intento)
    return ultimos


@estudiante_requerido
def ver_bloque(request, participante, concepto, bloque_id):
    if concepto not in NOMBRES_CONCEPTOS:
        raise Http404("Concepto desconocido")
    registro = BloqueRefuerzo.objects.filter(pk=bloque_id, concepto=concepto).first()
    # Un bloque sin validar no existe para el estudiante (HE3).
    if registro is None or not registro.validado:
        raise Http404("Bloque desconocido")
    estado = intervencion()
    if not concepto_abierto(participante, concepto, estado):
        return _bloqueado(
            request, participante, concepto, AperturaRefuerzo.CONCEPTO_BLOQUEADO, registro,
        )
    if not bloque_liberado(registro, estado):
        return _bloqueado(
            request, participante, concepto, AperturaRefuerzo.SEMANA_FUTURA, registro,
        )

    bloque = registro.bloque
    enviado = {}
    if request.method == "POST":
        ejercicio = bloque.ejercicio(request.POST.get("ejercicio", ""))
        if ejercicio is None:
            raise Http404("Ejercicio desconocido")
        codigo_solucion = request.POST.get("codigo", "")[:MAXIMO_CARACTERES]
        ejecucion = ejecutar_solucion(
            codigo_solucion, ejercicio, settings.TIEMPO_LIMITE_EJERCICIO,
            remoto=ejecutor_configurado(),
        )
        IntentoEjercicio.objects.create(
            analisis=participante.ultimo_analisis,
            concepto=concepto,
            bloque_id=registro.id,
            bloque_version=registro.version,
            ejercicio=ejercicio.id,
            longitud_codigo=len(codigo_solucion),
            hash_codigo=hashlib.sha256(codigo_solucion.encode("utf-8")).hexdigest(),
            ejecutado=ejecucion.error != NO_DISPONIBLE,
            pasados=ejecucion.pasados,
            total=ejecucion.total,
            error=ejecucion.error,
            casos=ejecucion.casos,
            usa_concepto=usa_concepto(codigo_solucion, concepto),
        )
        # El código vuelve solo en esta respuesta, para que el estudiante lo siga
        # corrigiendo; no se guarda en ningún lado.
        enviado = {ejercicio.id: codigo_solucion}
    else:
        AperturaRefuerzo.objects.create(
            participante=participante, concepto=concepto,
            bloque_id=registro.id, bloque_version=registro.version,
        )

    ultimos = _ultimos_intentos(participante, registro)
    return render(request, "refuerzo/bloque.html", {
        "nombre": NOMBRES_CONCEPTOS[concepto],
        "concepto": concepto,
        "bloque": bloque,
        "ejercicios": [
            {
                "datos": ejercicio,
                "intento": ultimos.get(ejercicio.id),
                "codigo": enviado.get(ejercicio.id, ejercicio.plantilla),
            }
            for ejercicio in bloque.ejercicios
        ],
    })


# Informe personal (RF-31, RF-34, D11)

def _estimacion(n_ia, n, valor):
    intervalo = intervalo_wilson(n_ia, n) if n and valor is not None else None
    return {
        "valor": valor,
        "n": n,
        "n_ia": n_ia,
        "intervalo": intervalo,
        "ancho": intervalo is not None and intervalo[1] - intervalo[0] > ANCHO_INTERPRETABLE,
    }


@estudiante_requerido
def informe(request, participante):
    """Solo al final: durante la intervención el estudiante no ve su IDC (D11)."""
    estado = intervencion()
    analisis = participante.ultimo_analisis
    if not estado.liberado or analisis is None:
        return render(request, "refuerzo/informe_no_disponible.html", status=403)
    asignacion = getattr(participante, "asignacion", None)
    intentos = IntentoEjercicio.objects.filter(analisis__participante=participante, ejecutado=True)
    return render(request, "refuerzo/informe.html", {
        "participante": participante,
        "analisis": analisis,
        "global": _estimacion(analisis.n_ia, analisis.n_fragmentos, analisis.idc_global),
        "conceptos": [
            {
                "nombre": NOMBRES_CONCEPTOS[c.concepto],
                "estado": ETIQUETAS_ESTADO.get(c.estado, c.estado),
                "reforzado": asignacion is not None and c.concepto in asignacion.reforzados,
                **_estimacion(c.n_ia, c.n_fragmentos, c.idc),
            }
            for c in analisis.conceptos.all()
        ],
        "practica": {
            "ejercicios": intentos.values("bloque_id", "ejercicio").distinct().count(),
            "resueltos": sum(
                1 for _ in {(i.bloque_id, i.ejercicio) for i in intentos if i.resuelto}
            ),
        },
    })


# Exportaciones del investigador

@login_required
def exportar_intentos(request):
    return respuesta_csv(exportar_csv_intentos(), "intentos_idc.csv")


@login_required
def exportar_aperturas(request):
    return respuesta_csv(exportar_csv_aperturas(), "aperturas_idc.csv")


@login_required
def exportar_adherencia(request):
    return respuesta_csv(exportar_csv_adherencia(), "adherencia_idc.csv")
