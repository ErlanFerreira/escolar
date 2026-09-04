from datetime import date

from django.views.generic import TemplateView

from apps.accounts.models import CustomUser
from apps.alunos.models import Aluno
from apps.comunicacao.utils import contar_nao_lidos
from apps.core.mixins import RoleRequiredMixin
from apps.escola.models import Turma
from apps.financeiro.models import Cobranca
from apps.frequencia.relatorio import calcular_frequencia
from apps.notas.boletim import montar_boletim


class SecretariaDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/secretaria.html"
    allowed_roles = (CustomUser.Role.SECRETARIA, CustomUser.Role.DIRETOR)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cobrancas_atrasadas = Cobranca.objects.filter(
            status=Cobranca.Status.PENDENTE, data_vencimento__lt=date.today()
        )
        context["total_alunos_ativos"] = Aluno.objects.filter(ativo=True).count()
        context["total_turmas_ativas"] = Turma.objects.filter(ano_letivo__ativo=True).count()
        context["total_cobrancas_atrasadas"] = cobrancas_atrasadas.count()
        context["valor_atrasado"] = sum((c.valor_final for c in cobrancas_atrasadas), start=0)
        context["comunicados_nao_lidos"] = contar_nao_lidos(self.request.user)
        return context


class ProfessorDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/professor.html"
    allowed_roles = (CustomUser.Role.PROFESSOR,)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["minhas_turmas"] = Turma.objects.for_user(self.request.user).select_related(
            "serie", "ano_letivo"
        )
        context["comunicados_nao_lidos"] = contar_nao_lidos(self.request.user)
        return context


class ResponsavelDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/responsavel.html"
    allowed_roles = (CustomUser.Role.RESPONSAVEL,)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["meus_filhos"] = Aluno.objects.for_user(self.request.user)
        cobrancas_atrasadas = Cobranca.objects.for_user(self.request.user).filter(
            status=Cobranca.Status.PENDENTE, data_vencimento__lt=date.today()
        )
        context["total_cobrancas_atrasadas"] = cobrancas_atrasadas.count()
        context["valor_atrasado"] = sum((c.valor_final for c in cobrancas_atrasadas), start=0)
        context["comunicados_nao_lidos"] = contar_nao_lidos(self.request.user)
        return context


class AlunoDashboardView(RoleRequiredMixin, TemplateView):
    template_name = "dashboard/aluno.html"
    allowed_roles = (CustomUser.Role.ALUNO,)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aluno = Aluno.objects.filter(user=self.request.user).first()
        context["comunicados_nao_lidos"] = contar_nao_lidos(self.request.user)
        context["media_geral"] = None
        context["frequencia_geral"] = None
        if aluno:
            boletim = montar_boletim(aluno)
            medias = [item["media"] for item in boletim if item["media"] is not None]
            context["media_geral"] = sum(medias) / len(medias) if medias else None

            frequencia = calcular_frequencia(aluno)
            percentuais = [item["percentual"] for item in frequencia if item["percentual"] is not None]
            context["frequencia_geral"] = sum(percentuais) / len(percentuais) if percentuais else None
        return context
