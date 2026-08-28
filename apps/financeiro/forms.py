from django import forms

from .models import Pagamento, PlanoPagamento


class GerarCobrancasForm(forms.Form):
    plano = forms.ModelChoiceField(
        label="Plano de pagamento", queryset=PlanoPagamento.objects.select_related("ano_letivo")
    )


class PagamentoForm(forms.ModelForm):
    class Meta:
        model = Pagamento
        fields = ["valor_pago", "data_pagamento", "forma_pagamento", "observacao"]
        widgets = {"data_pagamento": forms.DateInput(attrs={"type": "date"})}
