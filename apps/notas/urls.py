from django.urls import path

from . import views

app_name = "notas"

urlpatterns = [
    path("professor/turmas/<int:turma_id>/notas/", views.TurmaNotasView.as_view(), name="turma"),
    path(
        "professor/turmas/<int:turma_id>/disciplinas/<int:disciplina_id>/avaliacoes/nova/",
        views.AvaliacaoCreateView.as_view(),
        name="nova_avaliacao",
    ),
    path("professor/avaliacoes/<int:avaliacao_id>/lancar/", views.LancarNotasView.as_view(), name="lancar"),
    path("responsavel/filhos/<int:aluno_id>/notas/", views.BoletimAlunoView.as_view(), name="boletim_filho"),
    path("aluno/notas/", views.MeuBoletimView.as_view(), name="meu_boletim"),
]
