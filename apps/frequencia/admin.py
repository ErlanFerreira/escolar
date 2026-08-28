from django.contrib import admin

from .models import Aula, PresencaAluno


class PresencaAlunoInline(admin.TabularInline):
    model = PresencaAluno
    extra = 0
    autocomplete_fields = ["aluno"]


@admin.register(Aula)
class AulaAdmin(admin.ModelAdmin):
    list_display = ["turma", "disciplina", "professor", "data"]
    list_filter = ["turma", "disciplina", "data"]
    search_fields = ["turma__nome", "disciplina__nome"]
    autocomplete_fields = ["turma", "disciplina", "professor"]
    inlines = [PresencaAlunoInline]


@admin.register(PresencaAluno)
class PresencaAlunoAdmin(admin.ModelAdmin):
    list_display = ["aluno", "aula", "status"]
    list_filter = ["status", "aula__turma", "aula__disciplina"]
    search_fields = ["aluno__nome_completo"]
    autocomplete_fields = ["aluno", "aula"]
