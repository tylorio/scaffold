"""Une los servicios puros con la base de datos."""
from django.conf import settings
from django.db import transaction

from .models import Analisis, Configuracion, Fragmento, Participante, ResultadoConcepto
from .servicios.clasificador import cargar_modelo
from .servicios.conceptos import CONCEPTOS
from .servicios.exportacion import RegistroParticipante, generar_csv
from .servicios.flujo import ResultadoAnalisis, analizar_repositorio
from .servicios.idc import Parametros


def parametros_vigentes() -> Parametros:
    config = Configuracion.obtener()
    return Parametros(theta=config.theta, lambda_=config.lambda_valor, m=config.m)


def _guardar(
    participante: Participante, datos: ResultadoAnalisis, parametros, modelo
) -> Analisis:
    resultado = datos.resultado
    with transaction.atomic():
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
        )
        ResultadoConcepto.objects.bulk_create(
            ResultadoConcepto(
                analisis=analisis,
                concepto=c.concepto,
                n_fragmentos=c.n_fragmentos,
                n_ia=c.n_ia,
                idc=c.idc,
                estado=c.estado,
                reforzado=c.reforzado,
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


def ejecutar_analisis(participante: Participante) -> Analisis:
    parametros = parametros_vigentes()
    modelo = cargar_modelo(settings.RUTA_MODELO)
    datos = analizar_repositorio(
        participante.repositorio, modelo, parametros, base=settings.BASE_DIR,
    )
    return _guardar(participante, datos, parametros, modelo)


def _registro(participante: Participante) -> RegistroParticipante:
    analisis = participante.ultimo_analisis
    if analisis is None:
        return RegistroParticipante(codigo=participante.codigo)
    return RegistroParticipante(
        codigo=participante.codigo,
        fecha=analisis.fecha.isoformat(timespec="seconds"),
        n_fragmentos=analisis.n_fragmentos,
        idc_global=analisis.idc_global,
        theta=analisis.theta,
        lambda_=analisis.lambda_valor,
        m=analisis.m,
        modelo_version=analisis.modelo_version,
        modelo_es_demo=analisis.modelo_es_demo,
        conceptos=tuple(analisis.conceptos.all()),
    )


def exportar_csv() -> str:
    return generar_csv(_registro(p) for p in Participante.objects.all())
