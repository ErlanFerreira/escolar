from django import forms
from django.forms import modelformset_factory

from .models import Avaliacao, Nota, PeriodoLetivo


class AvaliacaoForm(forms.ModelForm):
    class Meta:
        model = Avaliacao
        fields = ["periodo", "tipo", "titulo", "data", "valor_maximo", "peso"]
        widgets = {"data": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, ano_letivo=None, **kwargs):
        super().__init__(*args, **kwargs)
        if ano_letivo is not None:
            self.fields["periodo"].queryset = PeriodoLetivo.objects.filter(ano_letivo=ano_letivo)


NotaFormSet = modelformset_factory(Nota, fields=["valor", "observacao"], extra=0)
