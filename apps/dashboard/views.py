from django.views.generic import TemplateView

from apps.accounts.models import CustomUser
from apps.alunos.models import Aluno
from apps.core.mixins import RoleRequiredMixin
from apps.escola.models import Turma


class SecretariaDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/secretaria.html"
    allowed_roles = (CustomUser.Role.SECRETARIA, CustomUser.Role.DIRETOR)


class ProfessorDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/professor.html"
    allowed_roles = (CustomUser.Role.PROFESSOR,)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["minhas_turmas"] = Turma.objects.for_user(self.request.user).select_related(
            "serie", "ano_letivo"
        )
        return context


class ResponsavelDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/responsavel.html"
    allowed_roles = (CustomUser.Role.RESPONSAVEL,)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meus_filhos"] = Aluno.objects.for_user(self.request.user)
        return context


class AlunoDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/aluno.html"
    allowed_roles = (CustomUser.Role.ALUNO,)
