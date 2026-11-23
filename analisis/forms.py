import re

from django import forms
from django.conf import settings
from django.core.validators import validate_email

from .models import Configuracion, Participante
from .servicios.autoria import hashes_de_correos
from .servicios.repositorio import OrigenInvalido, validar_origen


class ParticipanteForm(forms.ModelForm):
    correos = forms.CharField(
        label="Correos de commit",
        help_text=(
            "Los que el participante usa en sus commits, separados por comas. Solo se "
            "analizan sus funciones, y del correo solo se guarda una huella (HMAC)."
        ),
        widget=forms.TextInput(attrs={"placeholder": "correo@ejemplo.com"}),
    )

    class Meta:
        model = Participante
        fields = ["codigo", "repositorio", "consentimiento_en", "consentimiento_version"]
        help_texts = {
            "consentimiento_en": "Fecha en que firmó el consentimiento informado.",
            "consentimiento_version": "Versión del formulario aprobada por el CEI, p. ej. v1.",
        }
        widgets = {
            "consentimiento_en": forms.DateInput(attrs={"type": "date"}),
            "codigo": forms.TextInput(attrs={"placeholder": "P01"}),
            "repositorio": forms.TextInput(
                attrs={"placeholder": "demo_repo o https://..."}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sin consentimiento no se registra a nadie.
        self.fields["consentimiento_en"].required = True
        self.fields["consentimiento_version"].required = True

    def clean_repositorio(self):
        origen = self.cleaned_data["repositorio"].strip()
        try:
            validar_origen(origen, settings.BASE_DIR)
        except OrigenInvalido as error:
            raise forms.ValidationError(str(error)) from error
        return origen

    def clean_correos(self):
        correos = [c for c in re.split(r"[\s,;]+", self.cleaned_data["correos"]) if c]
        for correo in correos:
            validate_email(correo)
        if not correos:
            raise forms.ValidationError("Indica al menos un correo.")
        return correos

    def save(self, commit=True):
        self.instance.hashes_correos = hashes_de_correos(
            self.cleaned_data["correos"], settings.SAL_CORREOS
        )
        return super().save(commit)


class ConfiguracionForm(forms.ModelForm):
    def __init__(self, *args, congelada=False, **kwargs):
        super().__init__(*args, **kwargs)
        modo = self.fields["modo"]
        modo.help_text = (
            "Se fija después del go/no-go del clasificador (semana 7). En modo "
            "exploratorio el sorteo no usa el caso A."
        )
        if congelada:
            modo.disabled = True
            modo.help_text = "La asignación ya está congelada: el modo no puede cambiar."

    class Meta:
        model = Configuracion
        fields = ["theta", "lambda_valor", "m", "modo"]
        widgets = {
            "theta": forms.NumberInput(attrs={"step": "0.01", "min": 0, "max": 1}),
            "lambda_valor": forms.NumberInput(
                attrs={"step": "0.01", "min": 0, "max": 1}
            ),
            "m": forms.NumberInput(attrs={"min": 1}),
        }
