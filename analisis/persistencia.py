"""Une los servicios puros con la base de datos."""
import secrets
from collections import Counter
from dataclasses import dataclass, field

from django.conf import settings
from django.db import transaction

from .models import (
    Analisis,
    Asignacion,
    Auditoria,
    Configuracion,
    Congelacion,
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
from .servicios.idc import (
    Parametros,
    ResultadoIDC,
    conjunto_elegible,
    derivar_semilla,
    repartir_conceptos,
    sortear_orden,
)
from .servicios.idc import ResultadoConcepto as ResultadoConceptoIDC

TAMANO_BLOQUE = 4


class RepositorioSinFunciones(Exception):
    """El repositorio se leyó bien, pero no tiene funciones Python que analizar."""


class SinCorreosDeclarados(Exception):
    """Sin correos de commit no se puede aplicar el filtro por autor (D19)."""


class AsignacionCongelada(Exception):
    """Después de congelar ya no se puede reanalizar ni volver a sortear (D3, R5)."""


class NoSePuedeCongelar(Exception):
    """Faltan condiciones para congelar: el modo o algún diagnóstico."""


def parametros_vigentes() -> Parametros:
    config = Configuracion.obtener()
    return Parametros(theta=config.theta, lambda_=config.lambda_valor, m=config.m)


def congelacion() -> Congelacion | None:
    return Congelacion.objects.first()


def exigir_asignacion_congelada() -> Congelacion:
    """Para lo que solo puede ocurrir después de congelar, como corregir el pretest."""
    actual = congelacion()
    if actual is None:
        raise NoSePuedeCongelar(
            "La asignación todavía no está congelada: congélala antes del pretest."
        )
    return actual


# Análisis

def _guardar(
    participante: Participante, datos: ResultadoAnalisis, parametros, modelo,
) -> Analisis:
    resultado = datos.resultado
    analisis = Analisis.objects.create(
        participante=participante,
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
        indice_historial=datos.indice_historial.proporcion_lineas,
        indice_historial_15=datos.indice_historial.proporcion_lineas_15,
        indice_historial_60=datos.indice_historial.proporcion_lineas_60,
        media_log_insercion=datos.indice_historial.media_log_insercion,
        n_lineas_con_historial=datos.indice_historial.n_lineas_con_historial,
        n_con_historial=datos.indice_historial.n_fragmentos_con_historial,
        umbral_historial=datos.indice_historial.umbral_lineas,
        version_historial=datos.indice_historial.version,
    )
    ResultadoConcepto.objects.bulk_create(
        ResultadoConcepto(
            analisis=analisis,
            concepto=c.concepto,
            n_fragmentos=c.n_fragmentos,
            n_ia=c.n_ia,
            idc=c.idc,
            estado=c.estado,
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


def _motivo_sin_fragmentos(datos: ResultadoAnalisis) -> str:
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


def ejecutar_analisis(participante: Participante, usuario: str = "web") -> Analisis:
    """Hace el diagnóstico. Antes de congelar, repetirlo reemplaza al anterior (R5)."""
    if congelacion() is not None:
        raise AsignacionCongelada(
            "La asignación ya está congelada: no se puede volver a analizar a "
            f"{participante.codigo}."
        )
    if not participante.hashes_correos:
        raise SinCorreosDeclarados(
            f"{participante.codigo} no tiene correos de commit declarados: sin ellos no "
            "se puede separar su código del de otros autores (D19)."
        )
    filtro = FiltroAutor(frozenset(participante.hashes_correos), settings.SAL_CORREOS)
    parametros = parametros_vigentes()
    modelo = cargar_modelo(settings.RUTA_MODELO)
    datos = analizar_repositorio(
        participante.repositorio, modelo, parametros, base=settings.BASE_DIR,
        filtro=filtro, temporal=settings.CARPETA_TEMPORAL,
    )
    # Un análisis vacío no reemplaza a uno válido anterior.
    if not datos.fragmentos:
        raise RepositorioSinFunciones(_motivo_sin_fragmentos(datos))
    with transaction.atomic():
        anteriores = [str(a.analisis_id) for a in participante.analisis.all()]
        participante.analisis.all().delete()
        nuevo = _guardar(participante, datos, parametros, modelo)
        if anteriores:
            Auditoria.anotar(
                usuario, Auditoria.REANALIZAR, participante.codigo,
                anteriores=anteriores, nuevo=str(nuevo.analisis_id),
            )
        return nuevo


# Congelación

def _resultado_idc(analisis: Analisis) -> ResultadoIDC:
    return ResultadoIDC(
        idc_global=analisis.idc_global,
        n_fragmentos=analisis.n_fragmentos,
        n_ia=analisis.n_ia,
        conceptos=tuple(
            ResultadoConceptoIDC(c.concepto, c.n_fragmentos, c.n_ia, c.idc, c.estado)
            for c in analisis.conceptos.all()
        ),
    )


@dataclass(frozen=True)
class EstadoCongelacion:
    congelada: Congelacion | None
    modo: str
    n_participantes: int
    sin_diagnostico: list[str] = field(default_factory=list)
    casos: dict[str, int] = field(default_factory=dict)  # vista previa: no depende del azar

    @property
    def faltantes(self) -> list[str]:
        motivos = []
        if not self.modo:
            motivos.append(
                "Fija el modo (confirmatorio o exploratorio) en Configuración, según el "
                "go/no-go del clasificador."
            )
        if not self.n_participantes:
            motivos.append("No hay participantes registrados.")
        if self.sin_diagnostico:
            motivos.append("Sin diagnóstico: " + ", ".join(self.sin_diagnostico) + ".")
        return motivos

    @property
    def lista(self) -> bool:
        return self.congelada is None and not self.faltantes

    @property
    def ordenes(self) -> tuple[int, int]:
        """Cuántos AB y BA habrá; con un número impar, uno de los dos tiene uno más."""
        return self.n_participantes // 2, self.n_participantes % 2


def estado_congelacion() -> EstadoCongelacion:
    modo = Configuracion.obtener().modo
    participantes = list(Participante.objects.prefetch_related("analisis__conceptos"))
    sin_diagnostico, casos = [], Counter()
    for participante in participantes:
        analisis = participante.ultimo_analisis
        if analisis is None:
            sin_diagnostico.append(participante.codigo)
        elif modo:
            casos[conjunto_elegible(_resultado_idc(analisis), modo)[0]] += 1
    return EstadoCongelacion(
        congelada=congelacion(),
        modo=modo,
        n_participantes=len(participantes),
        sin_diagnostico=sin_diagnostico,
        casos=dict(sorted(casos.items())),
    )


def congelar_asignacion(
    semilla_base: int | None = None, tamano_bloque: int = TAMANO_BLOQUE, usuario: str = "web",
) -> Congelacion:
    """Sortea y fija, una sola vez, los conceptos y el orden AB/BA de toda la muestra.

    Los conceptos de cada participante y el orden de la muestra usan flujos
    aleatorios distintos derivados de la misma semilla base (R2).
    """
    with transaction.atomic():
        estado = estado_congelacion()
        if estado.congelada is not None:
            raise AsignacionCongelada("La asignación ya se congeló.")
        if estado.faltantes:
            raise NoSePuedeCongelar(" ".join(estado.faltantes))

        base = secrets.randbelow(2**62) if semilla_base is None else semilla_base
        participantes = list(
            Participante.objects.order_by("codigo").prefetch_related("analisis__conceptos")
        )
        ordenes = sortear_orden([p.codigo for p in participantes], base, tamano_bloque)
        for participante in participantes:
            analisis = participante.ultimo_analisis
            resultado = _resultado_idc(analisis)
            reparto = repartir_conceptos(
                resultado, derivar_semilla(base, "conceptos", participante.codigo),
                estado.modo,
            )
            Asignacion.objects.create(
                participante=participante,
                analisis_base=analisis,
                semilla=reparto.semilla,
                debiles=resultado.debiles,
                reforzados=list(reparto.reforzados),
                control=list(reparto.control),
                caso=reparto.caso,
                modo=reparto.modo,
                orden=ordenes[participante.codigo],
            )
            analisis.conceptos.filter(concepto__in=reparto.reforzados).update(reforzado=True)
        hecha = Congelacion.objects.create(
            semilla_base=base, modo=estado.modo, tamano_bloque=tamano_bloque,
        )
        Auditoria.anotar(
            usuario, Auditoria.CONGELAR, modo=estado.modo, semilla_base=base,
            n_participantes=len(participantes), casos=estado.casos,
        )
        return hecha


# Exportación

def _registro(participante: Participante) -> RegistroParticipante:
    analisis = participante.ultimo_analisis
    if analisis is None:
        return RegistroParticipante(codigo=participante.codigo)
    asignacion = getattr(participante, "asignacion", None)
    return RegistroParticipante(
        codigo=participante.codigo,
        caso=asignacion.caso if asignacion else "",
        orden=asignacion.orden if asignacion else "",
        modo=asignacion.modo if asignacion else "",
        control=tuple(asignacion.control) if asignacion else (),
        fecha=analisis.fecha.isoformat(timespec="seconds"),
        n_fragmentos=analisis.n_fragmentos,
        n_ia=analisis.n_ia,
        n_autores=analisis.n_autores,
        n_triviales=analisis.n_triviales,
        idc_global=analisis.idc_global,
        indice_historial=analisis.indice_historial,
        indice_historial_15=analisis.indice_historial_15,
        indice_historial_60=analisis.indice_historial_60,
        media_log_insercion=analisis.media_log_insercion,
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
                "fecha": a.fecha.isoformat(timespec="seconds"),
                "concepto": c.concepto,
                "condicion": asignacion.condicion(c.concepto) if asignacion else "",
                "caso": asignacion.caso if asignacion else "",
                "orden": asignacion.orden if asignacion else "",
                "modo": asignacion.modo if asignacion else "",
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
