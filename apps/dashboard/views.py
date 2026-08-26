from django.views.generic import TemplateView

from apps.accounts.models import CustomUser
from apps.core.mixins import RoleRequiredMixin


class SecretariaDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/secretaria.html"
    allowed_roles = (CustomUser.Role.SECRETARIA, CustomUser.Role.DIRETOR)


class ProfessorDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/professor.html"
    allowed_roles = (CustomUser.Role.PROFESSOR,)


class ResponsavelDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/responsavel.html"
    allowed_roles = (CustomUser.Role.RESPONSAVEL,)


class AlunoDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/aluno.html"
    allowed_roles = (CustomUser.Role.ALUNO,)
