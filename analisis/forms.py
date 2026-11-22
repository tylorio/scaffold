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
        fields = ["codigo", "repositorio"]
        widgets = {
            "codigo": forms.TextInput(attrs={"placeholder": "P01"}),
            "repositorio": forms.TextInput(
                attrs={"placeholder": "demo_repo o https://..."}
            ),
        }

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
    class Meta:
        model = Configuracion
        fields = ["theta", "lambda_valor", "m"]
        widgets = {
            "theta": forms.NumberInput(attrs={"step": "0.01", "min": 0, "max": 1}),
            "lambda_valor": forms.NumberInput(
                attrs={"step": "0.01", "min": 0, "max": 1}
            ),
            "m": forms.NumberInput(attrs={"min": 1}),
        }
