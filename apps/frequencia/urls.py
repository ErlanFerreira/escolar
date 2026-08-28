from django.urls import path

from . import views

app_name = "frequencia"

urlpatterns = [
    path("professor/turmas/<int:turma_id>/frequencia/", views.TurmaChamadaView.as_view(), name="turma"),
    path(
        "professor/turmas/<int:turma_id>/disciplinas/<int:disciplina_id>/chamada/",
        views.ChamadaView.as_view(),
        name="chamada",
    ),
    path(
        "responsavel/filhos/<int:aluno_id>/frequencia/",
        views.FrequenciaAlunoView.as_view(),
        name="relatorio_filho",
    ),
    path("aluno/frequencia/", views.MinhaFrequenciaView.as_view(), name="minha_frequencia"),
]
