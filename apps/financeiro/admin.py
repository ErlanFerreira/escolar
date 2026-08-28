from django.contrib import admin

from .models import Cobranca, Pagamento, PlanoPagamento


class PagamentoInline(admin.StackedInline):
    model = Pagamento
    extra = 0
    autocomplete_fields = ["registrado_por"]


@admin.register(PlanoPagamento)
class PlanoPagamentoAdmin(admin.ModelAdmin):
    list_display = ["nome", "ano_letivo", "valor_mensalidade", "dia_vencimento", "numero_parcelas"]
    list_filter = ["ano_letivo"]
    search_fields = ["nome"]


@admin.register(Cobranca)
class CobrancaAdmin(admin.ModelAdmin):
    list_display = ["aluno", "competencia", "valor_final", "data_vencimento", "status"]
    list_filter = ["status", "plano", "competencia"]
    search_fields = ["aluno__nome_completo", "competencia"]
    autocomplete_fields = ["aluno", "plano", "responsavel_financeiro"]
    inlines = [PagamentoInline]


@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ["cobranca", "valor_pago", "data_pagamento", "forma_pagamento"]
    list_filter = ["forma_pagamento"]
    autocomplete_fields = ["cobranca", "registrado_por"]
