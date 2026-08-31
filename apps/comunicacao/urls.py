from django.urls import path

from . import views

app_name = "comunicacao"

urlpatterns = [
    path("comunicados/", views.ComunicadoListView.as_view(), name="lista"),
    path("comunicados/novo/", views.ComunicadoCreateView.as_view(), name="criar"),
    path("comunicados/<int:pk>/", views.ComunicadoDetailView.as_view(), name="detalhe"),
]
