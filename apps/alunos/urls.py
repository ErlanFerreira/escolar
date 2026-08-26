from django.urls import path

from . import views

app_name = "alunos"

urlpatterns = [
    path("secretaria/alunos/", views.AlunoListView.as_view(), name="lista"),
    path("secretaria/alunos/matricular/", views.MatriculaWizardView.as_view(), name="matricular"),
    path("secretaria/alunos/<int:pk>/", views.AlunoDetailView.as_view(), name="detalhe"),
]
