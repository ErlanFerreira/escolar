from django.urls import path

from . import views

app_name = "financeiro"

urlpatterns = [
    path("secretaria/financeiro/", views.CobrancaListView.as_view(), name="lista"),
    path("secretaria/financeiro/gerar/", views.GerarCobrancasView.as_view(), name="gerar"),
    path("secretaria/financeiro/inadimplencia/", views.InadimplenciaView.as_view(), name="inadimplencia"),
    path(
        "secretaria/financeiro/cobrancas/<int:cobranca_id>/pagar/",
        views.RegistrarPagamentoView.as_view(),
        name="pagar",
    ),
    path("responsavel/financeiro/", views.MinhasCobrancasView.as_view(), name="minhas_cobrancas"),
]
