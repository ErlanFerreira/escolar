from django.contrib import admin
from solo.admin import SingletonModelAdmin

from .models import AnoLetivo, Disciplina, Escola, MatrizCurricular, Serie, Turma


@admin.register(Escola)
class EscolaAdmin(SingletonModelAdmin):
    pass


@admin.register(AnoLetivo)
class AnoLetivoAdmin(admin.ModelAdmin):
    list_display = ["ano", "status", "ativo", "data_inicio", "data_fim"]
    list_filter = ["status", "ativo"]


@admin.register(Serie)
class SerieAdmin(admin.ModelAdmin):
    list_display = ["nome", "segmento", "ordem"]
    list_filter = ["segmento"]
    ordering = ["ordem"]


@admin.register(Turma)
class TurmaAdmin(admin.ModelAdmin):
    list_display = ["__str__", "ano_letivo", "serie", "turno", "capacidade_maxima"]
    list_filter = ["ano_letivo", "serie", "turno"]
    search_fields = ["nome"]


@admin.register(Disciplina)
class DisciplinaAdmin(admin.ModelAdmin):
    list_display = ["nome", "codigo", "carga_horaria_semanal"]
    search_fields = ["nome", "codigo"]


@admin.register(MatrizCurricular)
class MatrizCurricularAdmin(admin.ModelAdmin):
    list_display = ["ano_letivo", "serie", "disciplina", "carga_horaria_anual"]
    list_filter = ["ano_letivo", "serie"]
