from django.contrib import admin

from .models import Professor, ProfessorDisciplinaTurma


class ProfessorDisciplinaTurmaInline(admin.TabularInline):
    model = ProfessorDisciplinaTurma
    extra = 1
    autocomplete_fields = ["turma", "disciplina"]


@admin.register(Professor)
class ProfessorAdmin(admin.ModelAdmin):
    list_display = ["__str__", "formacao", "ativo"]
    list_filter = ["ativo"]
    search_fields = ["user__first_name", "user__last_name", "user__email", "cpf"]
    autocomplete_fields = ["user"]
    filter_horizontal = ["disciplinas"]
    inlines = [ProfessorDisciplinaTurmaInline]


@admin.register(ProfessorDisciplinaTurma)
class ProfessorDisciplinaTurmaAdmin(admin.ModelAdmin):
    list_display = ["professor", "turma", "disciplina", "ano_letivo"]
    list_filter = ["ano_letivo", "turma", "disciplina"]
    autocomplete_fields = ["professor", "turma", "disciplina"]
