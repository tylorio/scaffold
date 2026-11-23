import uuid

from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

from .servicios.conceptos import NOMBRES_CONCEPTOS
from .servicios.idc import (
    CASO_A,
    CASO_B,
    CASO_C,
    CONFIRMATORIO,
    ETIQUETAS_ESTADO,
    EXPLORATORIO,
    intervalo_wilson,
)

MODOS = [
    (CONFIRMATORIO, "Confirmatorio (F1 ≥ 0,70)"),
    (EXPLORATORIO, "Exploratorio (F1 < 0,70)"),
]
CASOS = [
    (CASO_A, "A: entre los débiles"),
    (CASO_B, "B: entre los calculables"),
    (CASO_C, "C: entre los tres conceptos"),
]
ORDENES = [("AB", "Pretest A, postest B"), ("BA", "Pretest B, postest A")]

CODIGO_ANONIMO = RegexValidator(
    r"^[A-Z]{1,3}\d{2,4}$",
    "Usa solo un código anónimo, como P01. Nunca un nombre real.",
)


class Configuracion(models.Model):
    """Parámetros vigentes; siempre hay una sola fila (pk=1)."""

    theta = models.FloatField(
        "θ (umbral de P(IA))", default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    lambda_valor = models.FloatField(
        "λ (umbral de IDC)", default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )
    m = models.PositiveIntegerField(
        "m (fragmentos mínimos)", default=5, validators=[MinValueValidator(1)],
    )
    # Se fija tras el go/no-go del clasificador (semana 7) y no cambia después de congelar (R3).
    modo = models.CharField(max_length=13, choices=MODOS, blank=True)
    # Intervención (D20): los bloques se liberan por semana contada desde esta fecha.
    inicio_intervencion = models.DateField("inicio de la intervención", null=True, blank=True)
    # Lista de espera (D4): tras el postest se abre el material de todos los conceptos.
    control_liberado_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "configuración"

    @classmethod
    def obtener(cls):
        return cls.objects.get_or_create(pk=1)[0]


class Participante(models.Model):
    # Motivos para dejar a alguien fuera de la muestra (D15). Sin texto libre: un
    # comentario podría llevar un nombre.
    ETIQUETADO = "etiquetado"
    PILOTO = "piloto"
    NO_CUMPLE = "no_cumple"
    MOTIVOS_EXCLUSION = [
        (ETIQUETADO, "Participó en la sesión de etiquetado"),
        (PILOTO, "Participó en el piloto"),
        (NO_CUMPLE, "No cumple los criterios de inclusión"),
    ]

    codigo = models.CharField(
        "código anónimo", max_length=8, unique=True, validators=[CODIGO_ANONIMO],
    )
    repositorio = models.CharField("ruta local o URL del repositorio", max_length=500)
    # HMAC con sal de los correos de commit que declaró el participante (D19). Nunca en claro.
    hashes_correos = models.JSONField(default=list)
    # Hash del código de acceso del estudiante al portal (08 §3.2). El código no se guarda.
    codigo_acceso = models.CharField(max_length=128, blank=True)
    # Consentimiento informado firmado (en papel o en el formulario del CEI). Sin
    # él no se analiza el repositorio.
    consentimiento_en = models.DateField("fecha del consentimiento", null=True, blank=True)
    consentimiento_version = models.CharField(
        "versión del consentimiento", max_length=20, blank=True,
    )
    motivo_exclusion = models.CharField(
        "motivo de exclusión", max_length=12, choices=MOTIVOS_EXCLUSION, blank=True,
    )
    excluido_en = models.DateTimeField(null=True, blank=True)
    # Retiro voluntario (D13): se borran sus datos y queda solo el código, para el
    # diagrama de flujo de participantes.
    retirado_en = models.DateTimeField(null=True, blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["codigo"]

    @property
    def excluido(self):
        return bool(self.motivo_exclusion)

    @property
    def en_muestra(self):
        return not self.excluido and self.retirado_en is None

    def __str__(self):
        return self.codigo

    @property
    def ultimo_analisis(self):
        return self.analisis.first()


class Analisis(models.Model):
    """El diagnóstico de un participante. Hay uno solo válido por participante (R5).

    Guarda los parámetros usados para poder reproducirlo.
    """

    participante = models.ForeignKey(
        Participante, on_delete=models.CASCADE, related_name="analisis",
    )
    # Única llave entre el portal y el almacén local (05 §3.6, ESC-16).
    analisis_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    fecha = models.DateTimeField(auto_now_add=True)
    theta = models.FloatField()
    lambda_valor = models.FloatField()
    m = models.PositiveIntegerField()
    modelo_version = models.CharField(max_length=50)
    modelo_es_demo = models.BooleanField()
    commit_head = models.CharField(max_length=40, blank=True)
    tiene_historial = models.BooleanField(default=False)
    archivos_con_error = models.JSONField(default=list)
    n_fragmentos = models.PositiveIntegerField()
    n_ia = models.PositiveIntegerField()
    idc_global = models.FloatField(null=True)
    n_autores = models.PositiveIntegerField(null=True)
    n_triviales = models.PositiveIntegerField(default=0)
    n_fragmentos_otros_autores = models.PositiveIntegerField(default=0)  # D19
    n_indexacion_indeterminada = models.PositiveIntegerField(default=0)  # R4
    version_reglas = models.CharField(max_length=30, blank=True)
    version_rasgos = models.CharField(max_length=30, blank=True)
    # Índice de delegación por historial (D9, P10): fuera del clasificador, exploratorio para HE1.
    indice_historial = models.FloatField(null=True)  # proporción de líneas, umbral a priori
    indice_historial_15 = models.FloatField(null=True)  # sensibilidad
    indice_historial_60 = models.FloatField(null=True)  # sensibilidad
    media_log_insercion = models.FloatField(null=True)  # medida continua, sin umbral
    n_lineas_con_historial = models.PositiveIntegerField(default=0)
    n_con_historial = models.PositiveIntegerField(default=0)  # fragmentos
    umbral_historial = models.PositiveIntegerField(null=True)
    version_historial = models.CharField(max_length=30, blank=True)

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name_plural = "análisis"

    def __str__(self):
        return f"{self.participante} · {self.fecha:%Y-%m-%d %H:%M}"

    @property
    def intervalo(self):
        return intervalo_wilson(self.n_ia, self.n_fragmentos)


class Auditoria(models.Model):
    """Registro inmutable de las acciones que cambian el estudio (08 §3.5)."""

    CONGELAR = "congelar"
    REANALIZAR = "reanalizar"
    EXPORTAR = "exportar_resultados"
    IMPORTAR = "importar_resultados"
    CODIGO_ACCESO = "codigo_acceso"
    INICIO_INTERVENCION = "inicio_intervencion"
    LIBERAR_CONTROL = "liberar_control"
    CARGAR_BLOQUE = "cargar_bloque"
    VALIDAR_BLOQUE = "validar_bloque"
    EXCLUIR = "excluir"
    INCLUIR = "incluir"
    RETIRO = "retiro"
    EXPORTAR_ESTUDIO = "exportar_estudio"
    CIERRE = "cierre"
    ACCIONES = [
        (CONGELAR, "Congelar la asignación"),
        (REANALIZAR, "Reemplazar un diagnóstico"),
        (EXPORTAR, "Exportar resultados"),
        (IMPORTAR, "Importar resultados"),
        (CODIGO_ACCESO, "Generar un código de acceso"),
        (INICIO_INTERVENCION, "Fijar el inicio de la intervención"),
        (LIBERAR_CONTROL, "Liberar el material tras el postest"),
        (CARGAR_BLOQUE, "Cargar un bloque de refuerzo"),
        (VALIDAR_BLOQUE, "Validar un bloque de refuerzo"),
        (EXCLUIR, "Excluir a un participante de la muestra"),
        (INCLUIR, "Quitar una exclusión"),
        (RETIRO, "Retiro de un participante y borrado de sus datos"),
        (EXPORTAR_ESTUDIO, "Exportar la base para el análisis"),
        (CIERRE, "Cierre del estudio y borrado del código"),
    ]

    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=150)
    accion = models.CharField(max_length=30, choices=ACCIONES)
    objeto = models.CharField(max_length=100, blank=True)  # código anónimo, nunca un nombre
    detalle = models.JSONField(default=dict)

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name_plural = "auditoría"

    @classmethod
    def anotar(cls, usuario, accion, objeto="", **detalle):
        return cls.objects.create(usuario=usuario, accion=accion, objeto=objeto, detalle=detalle)


class Importacion(models.Model):
    """Archivo de resultados importado en el portal (ESC-15, ESC-18)."""

    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.CharField(max_length=150)
    esquema = models.CharField(max_length=20)
    hash_archivo = models.CharField(max_length=64, unique=True)
    n_participantes = models.PositiveIntegerField()
    generado = models.CharField(max_length=40)  # fecha en que el núcleo produjo el archivo

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name = "importación"
        verbose_name_plural = "importaciones"


class Congelacion(models.Model):
    """El momento único en que se sortea y fija la asignación de toda la muestra (D3).

    Existe a lo sumo una fila. Desde ese momento no se puede reanalizar a nadie.
    """

    fecha = models.DateTimeField(auto_now_add=True)
    semilla_base = models.BigIntegerField()
    modo = models.CharField(max_length=13, choices=MODOS)
    tamano_bloque = models.PositiveSmallIntegerField()

    class Meta:
        verbose_name = "congelación"
        verbose_name_plural = "congelación"

    def __str__(self):
        return f"{self.fecha:%Y-%m-%d %H:%M} · {self.modo}"


class Asignacion(models.Model):
    """Reparto entre refuerzo y control de un participante, y su orden de formas.

    Se crea al congelar (`congelar_asignacion`) y no cambia después. Su fecha es la
    de la congelación, anterior al pretest (D3).
    """

    participante = models.OneToOneField(
        Participante, on_delete=models.CASCADE, related_name="asignacion",
    )
    analisis_base = models.ForeignKey(
        Analisis, on_delete=models.RESTRICT, related_name="+",
    )
    semilla = models.BigIntegerField()  # derivada de la semilla base y del código
    debiles = models.JSONField(default=list)
    reforzados = models.JSONField(default=list)
    control = models.JSONField(default=list)
    caso = models.CharField(max_length=1, choices=CASOS)
    modo = models.CharField(max_length=13, choices=MODOS)
    orden = models.CharField(max_length=2, choices=ORDENES)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "asignación"
        verbose_name_plural = "asignaciones"

    def __str__(self):
        return f"{self.participante}"

    def condicion(self, concepto):
        if concepto in self.reforzados:
            return "reforzado"
        return "control" if concepto in self.control else "sin_asignar"

    @property
    def nombres_reforzados(self):
        return [NOMBRES_CONCEPTOS[c] for c in self.reforzados]

    @property
    def nombres_control(self):
        return [NOMBRES_CONCEPTOS[c] for c in self.control]


class ResultadoConcepto(models.Model):
    CONCEPTOS = list(NOMBRES_CONCEPTOS.items())
    ESTADOS = list(ETIQUETAS_ESTADO.items())

    analisis = models.ForeignKey(
        Analisis, on_delete=models.CASCADE, related_name="conceptos",
    )
    concepto = models.CharField(max_length=20, choices=CONCEPTOS)
    n_fragmentos = models.PositiveIntegerField()
    n_ia = models.PositiveIntegerField()
    idc = models.FloatField(null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS)
    reforzado = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]
        constraints = [
            models.UniqueConstraint(
                fields=["analisis", "concepto"], name="concepto_unico_por_analisis",
            ),
        ]

    @property
    def intervalo(self):
        return None if self.idc is None else intervalo_wilson(self.n_ia, self.n_fragmentos)


class Fragmento(models.Model):
    analisis = models.ForeignKey(
        Analisis, on_delete=models.CASCADE, related_name="fragmentos",
    )
    archivo = models.CharField(max_length=500)
    nombre = models.CharField(max_length=300)
    codigo = models.TextField()
    linea_inicio = models.PositiveIntegerField()
    linea_fin = models.PositiveIntegerField()
    lineas = models.PositiveIntegerField()
    complejidad = models.PositiveIntegerField()
    conceptos = models.JSONField(default=list)
    insercion_commit = models.PositiveIntegerField(null=True)
    p_ia = models.FloatField()

    class Meta:
        ordering = ["-p_ia", "archivo", "linea_inicio"]

    @property
    def nombres_conceptos(self):
        return [NOMBRES_CONCEPTOS[c] for c in self.conceptos]
