from django.contrib import admin

from .models import Aluno, AlunoResponsavel, Matricula, Responsavel


class AlunoResponsavelInline(admin.TabularInline):
    model = AlunoResponsavel
    extra = 1
    autocomplete_fields = ["responsavel"]


class MatriculaInline(admin.TabularInline):
    model = Matricula
    extra = 0
    autocomplete_fields = ["turma"]


@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    list_display = ["nome_completo", "matricula_numero", "data_nascimento", "ativo"]
    list_filter = ["ativo", "sexo"]
    search_fields = ["nome_completo", "matricula_numero", "cpf"]
    inlines = [AlunoResponsavelInline, MatriculaInline]


@admin.register(Responsavel)
class ResponsavelAdmin(admin.ModelAdmin):
    list_display = ["nome_completo", "cpf", "telefone", "email"]
    search_fields = ["nome_completo", "cpf", "email"]
    inlines = [AlunoResponsavelInline]


@admin.register(Matricula)
class MatriculaAdmin(admin.ModelAdmin):
    list_display = ["aluno", "turma", "ano_letivo", "status", "data_matricula"]
    list_filter = ["ano_letivo", "status", "turma"]
    search_fields = ["aluno__nome_completo", "aluno__matricula_numero"]
    autocomplete_fields = ["aluno", "turma"]
