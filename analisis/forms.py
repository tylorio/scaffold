from django import forms
from django.conf import settings

from .models import Configuracion, Participante
from .servicios.repositorio import OrigenInvalido, validar_origen


class ParticipanteForm(forms.ModelForm):
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
