from django import forms

from .models import Comunicado


class ComunicadoForm(forms.ModelForm):
    class Meta:
        model = Comunicado
        fields = ["titulo", "corpo", "publico_alvo", "turmas", "urgente", "anexo"]
        widgets = {"corpo": forms.Textarea(attrs={"rows": 6})}
