from django.contrib import admin

from .models import Avaliacao, Nota, PeriodoLetivo, TipoAvaliacao


@admin.register(TipoAvaliacao)
class TipoAvaliacaoAdmin(admin.ModelAdmin):
    list_display = ["nome", "peso"]


@admin.register(PeriodoLetivo)
class PeriodoLetivoAdmin(admin.ModelAdmin):
    list_display = ["nome", "ano_letivo", "numero", "data_inicio", "data_fim"]
    list_filter = ["ano_letivo"]


@admin.register(Avaliacao)
class AvaliacaoAdmin(admin.ModelAdmin):
    list_display = ["titulo", "turma", "disciplina", "professor", "periodo", "data"]
    list_filter = ["periodo", "turma", "disciplina"]
    search_fields = ["titulo"]
    autocomplete_fields = ["turma", "disciplina", "professor"]


@admin.register(Nota)
class NotaAdmin(admin.ModelAdmin):
    list_display = ["aluno", "avaliacao", "valor"]
    list_filter = ["avaliacao__turma", "avaliacao__disciplina"]
    search_fields = ["aluno__nome_completo"]
    autocomplete_fields = ["aluno", "avaliacao"]
