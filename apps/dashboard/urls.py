from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("secretaria/", views.SecretariaDashboardView.as_view(), name="secretaria"),
    path("professor/", views.ProfessorDashboardView.as_view(), name="professor"),
    path("responsavel/", views.ResponsavelDashboardView.as_view(), name="responsavel"),
    path("aluno/", views.AlunoDashboardView.as_view(), name="aluno"),
]
