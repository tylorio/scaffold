from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

from .servicios.conceptos import NOMBRES_CONCEPTOS
from .servicios.idc import ETIQUETAS_ESTADO, intervalo_wilson

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

    class Meta:
        verbose_name = "configuración"

    @classmethod
    def obtener(cls):
        return cls.objects.get_or_create(pk=1)[0]


class Participante(models.Model):
    codigo = models.CharField(
        "código anónimo", max_length=8, unique=True, validators=[CODIGO_ANONIMO],
    )
    repositorio = models.CharField("ruta local o URL del repositorio", max_length=500)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["codigo"]

    def __str__(self):
        return self.codigo

    @property
    def ultimo_analisis(self):
        return self.analisis.first()


class Analisis(models.Model):
    """Una corrida. Guarda los parámetros usados para poder reproducirla."""

    participante = models.ForeignKey(
        Participante, on_delete=models.CASCADE, related_name="analisis",
    )
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

    class Meta:
        ordering = ["-fecha", "-id"]
        verbose_name_plural = "análisis"

    def __str__(self):
        return f"{self.participante} · {self.fecha:%Y-%m-%d %H:%M}"

    @property
    def intervalo(self):
        return intervalo_wilson(self.n_ia, self.n_fragmentos)


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
