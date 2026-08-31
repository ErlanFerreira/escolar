from django.contrib import admin

from .models import Comunicado, ComunicadoLeitura


@admin.register(Comunicado)
class ComunicadoAdmin(admin.ModelAdmin):
    list_display = ["titulo", "autor", "publico_alvo", "data_publicacao", "urgente"]
    list_filter = ["publico_alvo", "urgente"]
    search_fields = ["titulo"]
    filter_horizontal = ["turmas"]
    autocomplete_fields = ["autor"]


@admin.register(ComunicadoLeitura)
class ComunicadoLeituraAdmin(admin.ModelAdmin):
    list_display = ["comunicado", "user", "lida_em"]
    list_filter = ["comunicado"]
    autocomplete_fields = ["comunicado", "user"]
