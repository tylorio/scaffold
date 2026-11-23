from django.db import models

from analisis.models import Analisis, Participante, ResultadoConcepto

from .servicios.banco import desde_json


class BloqueRefuerzo(models.Model):
    """Un bloque del banco de refuerzo (D20). El contenido se carga desde JSON.

    Cambiar el contenido exige subir la versión, y una versión nueva vuelve a quedar
    sin validar: solo se entregan bloques validados por los jueces (HE3).
    """

    id = models.CharField(max_length=60, primary_key=True)
    concepto = models.CharField(max_length=20, choices=ResultadoConcepto.CONCEPTOS)
    semana = models.PositiveSmallIntegerField()
    orden = models.PositiveSmallIntegerField()
    version = models.PositiveIntegerField()
    huella = models.CharField(max_length=64)  # SHA-256 del JSON de esta versión
    contenido = models.JSONField()
    validado = models.BooleanField(default=False)
    n_jueces = models.PositiveSmallIntegerField(null=True, blank=True)
    validado_en = models.DateTimeField(null=True, blank=True)
    validado_por = models.CharField(max_length=150, blank=True)
    cargado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["concepto", "semana", "orden"]
        constraints = [
            models.UniqueConstraint(
                fields=["concepto", "semana", "orden"], name="un_bloque_por_ranura",
            ),
        ]

    def __str__(self):
        return f"{self.id} v{self.version}"

    @property
    def bloque(self):
        return desde_json(self.contenido)

    @property
    def n_ejercicios(self):
        return len(self.contenido["ejercicios"])


class AperturaRefuerzo(models.Model):
    """Cada vez que un participante abre un bloque, o intenta abrir uno que no le toca.

    Las aperturas permitidas miden la exposición real. Las no permitidas (concepto
    de control antes del postest, bloque de una semana futura) se guardan para
    reportar los intentos de contaminación (D4, 21b §5).
    """

    CONCEPTO_BLOQUEADO = "concepto"
    SEMANA_FUTURA = "semana"
    MOTIVOS = [
        (CONCEPTO_BLOQUEADO, "Concepto no reforzado antes del postest"),
        (SEMANA_FUTURA, "Bloque de una semana que aún no empieza"),
    ]

    participante = models.ForeignKey(
        Participante, on_delete=models.CASCADE, related_name="aperturas",
    )
    concepto = models.CharField(max_length=20, choices=ResultadoConcepto.CONCEPTOS)
    bloque_id = models.CharField(max_length=60, blank=True)  # vacío: la lista del concepto
    bloque_version = models.PositiveIntegerField(null=True, blank=True)
    permitida = models.BooleanField(default=True)
    motivo = models.CharField(max_length=10, choices=MOTIVOS, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["fecha", "id"]


class IntentoAcceso(models.Model):
    """Cada intento de entrar al portal, para bloquear a quien prueba códigos al azar.

    La IP se guarda solo como hash y los registros se borran a las 24 h (08 §3.2).
    """

    ip_hash = models.CharField(max_length=64, db_index=True)
    fecha = models.DateTimeField(auto_now_add=True, db_index=True)
    exito = models.BooleanField(default=False)
    participante = models.ForeignKey(
        Participante, null=True, on_delete=models.SET_NULL, related_name="+",
    )


class IntentoEjercicio(models.Model):
    """Un envío de solución. El código no se guarda: solo su longitud y su hash (21b §5)."""

    analisis = models.ForeignKey(
        Analisis, on_delete=models.CASCADE, related_name="intentos",
    )
    concepto = models.CharField(max_length=20, choices=ResultadoConcepto.CONCEPTOS)
    bloque_id = models.CharField(max_length=60)
    bloque_version = models.PositiveIntegerField()
    ejercicio = models.CharField(max_length=20)
    longitud_codigo = models.PositiveIntegerField()
    hash_codigo = models.CharField(max_length=64)
    # False si el ejecutor no estaba disponible: no cuenta como intentado (P6).
    ejecutado = models.BooleanField(default=True)
    pasados = models.PositiveIntegerField()
    total = models.PositiveIntegerField()
    error = models.TextField(blank=True)
    casos = models.JSONField(default=list)
    usa_concepto = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha", "-id"]

    @property
    def resuelto(self):
        return self.ejecutado and self.total > 0 and self.pasados == self.total
