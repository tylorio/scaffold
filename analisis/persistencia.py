"""Une los servicios puros con la base de datos."""
import secrets

from django.conf import settings
from django.db import transaction

from .models import (
    Analisis,
    Asignacion,
    Configuracion,
    Fragmento,
    Participante,
    ResultadoConcepto,
)
from .servicios.autoria import FiltroAutor
from .servicios.clasificador import cargar_modelo
from .servicios.conceptos import CONCEPTOS, REGLAS_VERSION
from .servicios.exportacion import (
    RegistroParticipante,
    generar_csv,
    generar_csv_analisis,
)
from .servicios.flujo import ResultadoAnalisis, analizar_repositorio
from .servicios.idc import Parametros, repartir_conceptos
from .servicios.repositorio import ErrorRepositorio


class RepositorioSinFunciones(Exception):
    """El repositorio se leyó bien, pero no tiene funciones Python que analizar."""


class SinCorreosDeclarados(Exception):
    """Sin correos de commit no se puede aplicar el filtro por autor (D19)."""


def parametros_vigentes() -> Parametros:
    config = Configuracion.obtener()
    return Parametros(theta=config.theta, lambda_=config.lambda_valor, m=config.m)


def _sortear(participante: Participante, analisis: Analisis, debiles) -> Asignacion:
    semilla = secrets.randbelow(2**31)
    reparto = repartir_conceptos(debiles, semilla)
    return Asignacion.objects.create(
        participante=participante,
        analisis_base=analisis,
        semilla=semilla,
        debiles=list(debiles),
        reforzados=list(reparto.reforzados),
        control=list(reparto.control),
        comparable=reparto.comparable,
    )


def _guardar(
    participante: Participante, datos: ResultadoAnalisis, parametros, modelo,
    asignacion: Asignacion | None,
) -> Analisis:
    resultado = datos.resultado
    with transaction.atomic():
        analisis = Analisis.objects.create(
            participante=participante,
            fase=Analisis.PRE if asignacion is None else Analisis.POST,
            theta=parametros.theta,
            lambda_valor=parametros.lambda_,
            m=parametros.m,
            modelo_version=modelo.version,
            modelo_es_demo=modelo.es_demo,
            commit_head=datos.commit_head,
            tiene_historial=datos.tiene_historial,
            archivos_con_error=datos.archivos_con_error,
            n_fragmentos=resultado.n_fragmentos,
            n_ia=resultado.n_ia,
            idc_global=resultado.idc_global,
            n_autores=datos.n_autores,
            n_triviales=datos.n_triviales,
            n_fragmentos_otros_autores=datos.n_fragmentos_otros_autores,
            n_indexacion_indeterminada=datos.n_indexacion_indeterminada,
            version_reglas=REGLAS_VERSION,
            version_rasgos=modelo.rasgos_version,
            indice_historial=datos.indice_historial.valor,
            n_con_historial=datos.indice_historial.n_con_historial,
            umbral_historial=datos.indice_historial.umbral_lineas,
            version_historial=datos.indice_historial.version,
        )
        if asignacion is None:
            asignacion = _sortear(participante, analisis, resultado.debiles)
        ResultadoConcepto.objects.bulk_create(
            ResultadoConcepto(
                analisis=analisis,
                concepto=c.concepto,
                n_fragmentos=c.n_fragmentos,
                n_ia=c.n_ia,
                idc=c.idc,
                estado=c.estado,
                reforzado=c.concepto in asignacion.reforzados,
            )
            for c in resultado.conceptos
        )
        Fragmento.objects.bulk_create(
            Fragmento(
                analisis=analisis,
                archivo=c.fragmento.archivo,
                nombre=c.fragmento.nombre,
                codigo=c.fragmento.codigo,
                linea_inicio=c.fragmento.linea_inicio,
                linea_fin=c.fragmento.linea_fin,
                lineas=c.fragmento.lineas,
                complejidad=c.fragmento.complejidad,
                conceptos=[x for x in CONCEPTOS if x in c.fragmento.conceptos],
                insercion_commit=c.insercion_commit,
                p_ia=c.p_ia,
            )
            for c in datos.fragmentos
        )
    return analisis


def _motivo_sin_fragmentos(datos: ResultadoAnalisis, es_post: bool) -> str:
    if es_post:
        detalle = "No hay funciones nuevas desde el análisis pre."
    else:
        detalle = (
            "No se encontraron funciones Python para analizar en el repositorio "
            "(se omiten los archivos de pruebas y las funciones triviales)."
        )
    if datos.n_fragmentos_otros_autores:
        detalle += (
            f" Se descartaron {datos.n_fragmentos_otros_autores} funciones de otros "
            "autores: revisa los correos de commit declarados."
        )
    if datos.archivos_con_error:
        detalle += (
            " Archivos que no se pudieron leer: "
            + ", ".join(datos.archivos_con_error) + "."
        )
    return detalle + " No se guardó el análisis."


def ejecutar_analisis(participante: Participante) -> Analisis:
    """Hace el análisis pre, con su sorteo, o un post sobre el código nuevo."""
    if not participante.hashes_correos:
        raise SinCorreosDeclarados(
            f"{participante.codigo} no tiene correos de commit declarados: sin ellos no "
            "se puede separar su código del de otros autores (D19)."
        )
    filtro = FiltroAutor(frozenset(participante.hashes_correos), settings.SAL_CORREOS)
    asignacion = (
        Asignacion.objects.select_related("analisis_base")
        .filter(participante=participante).first()
    )
    desde_commit = None
    if asignacion is not None:
        desde_commit = asignacion.analisis_base.commit_head
        if not desde_commit:
            raise ErrorRepositorio(
                "El análisis pre se hizo sin historial Git: no se puede aislar el "
                "código nuevo."
            )
    parametros = parametros_vigentes()
    modelo = cargar_modelo(settings.RUTA_MODELO)
    datos = analizar_repositorio(
        participante.repositorio, modelo, parametros, base=settings.BASE_DIR,
        desde_commit=desde_commit, filtro=filtro,
    )
    # Un análisis vacío pasaría a ser el último y ocultaría uno válido anterior.
    if not datos.fragmentos:
        raise RepositorioSinFunciones(
            _motivo_sin_fragmentos(datos, asignacion is not None)
        )
    return _guardar(participante, datos, parametros, modelo, asignacion)


def _registro(participante: Participante) -> RegistroParticipante:
    analisis = participante.ultimo_analisis
    if analisis is None:
        return RegistroParticipante(codigo=participante.codigo)
    asignacion = getattr(participante, "asignacion", None)
    return RegistroParticipante(
        codigo=participante.codigo,
        fase=analisis.fase,
        comparable=asignacion.comparable if asignacion else None,
        control=tuple(asignacion.control) if asignacion else (),
        fecha=analisis.fecha.isoformat(timespec="seconds"),
        n_fragmentos=analisis.n_fragmentos,
        n_ia=analisis.n_ia,
        n_autores=analisis.n_autores,
        n_triviales=analisis.n_triviales,
        idc_global=analisis.idc_global,
        indice_historial=analisis.indice_historial,
        version_reglas=analisis.version_reglas,
        theta=analisis.theta,
        lambda_=analisis.lambda_valor,
        m=analisis.m,
        modelo_version=analisis.modelo_version,
        modelo_es_demo=analisis.modelo_es_demo,
        conceptos=tuple(analisis.conceptos.all()),
    )


def exportar_csv() -> str:
    return generar_csv(
        _registro(p) for p in Participante.objects.select_related("asignacion")
    )


def _filas_analisis():
    analisis = (
        Analisis.objects.select_related("participante__asignacion")
        .prefetch_related("conceptos")
        .order_by("participante__codigo", "fecha", "id")
    )
    for a in analisis:
        asignacion = getattr(a.participante, "asignacion", None)
        for c in a.conceptos.all():
            yield {
                "codigo": a.participante.codigo,
                "analisis": a.pk,
                "fase": a.fase,
                "fecha": a.fecha.isoformat(timespec="seconds"),
                "concepto": c.concepto,
                "condicion": asignacion.condicion(c.concepto) if asignacion else "",
                "comparable": int(asignacion.comparable) if asignacion else "",
                "semilla": asignacion.semilla if asignacion else "",
                "n_fragmentos": c.n_fragmentos,
                "n_ia": c.n_ia,
                "idc": c.idc,
                "estado": c.estado,
                "n_autores": "" if a.n_autores is None else a.n_autores,
                "theta": a.theta,
                "lambda": a.lambda_valor,
                "m": a.m,
                "modelo_version": a.modelo_version,
                "modelo_es_demo": int(a.modelo_es_demo),
                "version_reglas": a.version_reglas,
            }


def exportar_csv_analisis() -> str:
    return generar_csv_analisis(_filas_analisis())
