from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView

from apps.accounts.models import CustomUser
from apps.alunos.models import Aluno, Matricula
from apps.core.mixins import RoleRequiredMixin
from apps.escola.models import Turma
from apps.professores.models import Professor, ProfessorDisciplinaTurma

from .forms import PresencaFormSet
from .models import Aula, PresencaAluno
from .relatorio import calcular_frequencia


class TurmaChamadaView(RoleRequiredMixin, TemplateView):
    allowed_roles = (CustomUser.Role.PROFESSOR,)
    template_name = "frequencia/turma_chamada.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        turma = get_object_or_404(Turma.objects.for_user(self.request.user), pk=kwargs["turma_id"])
        atribuicoes = ProfessorDisciplinaTurma.objects.filter(
            professor__user=self.request.user, turma=turma
        ).select_related("disciplina")
        context["turma"] = turma
        context["atribuicoes"] = atribuicoes
        context["hoje"] = date.today()
        return context


class ChamadaView(RoleRequiredMixin, TemplateView):
    allowed_roles = (CustomUser.Role.PROFESSOR,)
    template_name = "frequencia/chamada.html"

    def dispatch(self, request, *args, **kwargs):
        self.turma = get_object_or_404(Turma.objects.for_user(request.user), pk=kwargs["turma_id"])
        get_object_or_404(
            ProfessorDisciplinaTurma,
            professor__user=request.user,
            turma=self.turma,
            disciplina_id=kwargs["disciplina_id"],
        )
        data_str = request.GET.get("data") or request.POST.get("data")
        self.data = date.fromisoformat(data_str) if data_str else date.today()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        aula = self._get_or_create_aula()
        formset = PresencaFormSet(queryset=self._queryset(aula))
        return self.render_to_response(self.get_context_data(formset=formset))

    def post(self, request, *args, **kwargs):
        aula = self._get_or_create_aula()
        formset = PresencaFormSet(request.POST, queryset=self._queryset(aula))
        if formset.is_valid():
            formset.save()
            messages.success(request, "Chamada salva com sucesso.")
            return redirect(f"{reverse('frequencia:turma', args=[self.turma.pk])}")
        return self.render_to_response(self.get_context_data(formset=formset))

    def _get_or_create_aula(self):
        aula, _ = Aula.objects.get_or_create(
            turma=self.turma,
            disciplina_id=self.kwargs["disciplina_id"],
            data=self.data,
            defaults={"professor": Professor.objects.get(user=self.request.user)},
        )
        alunos_ids = Matricula.objects.filter(
            turma=self.turma, ano_letivo=self.turma.ano_letivo, status=Matricula.Status.ATIVA
        ).values_list("aluno_id", flat=True)
        existentes_ids = set(PresencaAluno.objects.filter(aula=aula).values_list("aluno_id", flat=True))
        novos = [
            PresencaAluno(aula=aula, aluno_id=aluno_id)
            for aluno_id in alunos_ids
            if aluno_id not in existentes_ids
        ]
        if novos:
            PresencaAluno.objects.bulk_create(novos)
        return aula

    def _queryset(self, aula):
        return (
            PresencaAluno.objects.filter(aula=aula).select_related("aluno").order_by("aluno__nome_completo")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["turma"] = self.turma
        context["data"] = self.data
        return context


class FrequenciaAlunoView(RoleRequiredMixin, TemplateView):
    allowed_roles = (CustomUser.Role.SECRETARIA, CustomUser.Role.DIRETOR, CustomUser.Role.RESPONSAVEL)
    template_name = "frequencia/relatorio.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aluno = get_object_or_404(Aluno.objects.for_user(self.request.user), pk=kwargs["aluno_id"])
        context["aluno"] = aluno
        context["relatorio"] = calcular_frequencia(aluno)
        return context


class MinhaFrequenciaView(RoleRequiredMixin, TemplateView):
    allowed_roles = (CustomUser.Role.ALUNO,)
    template_name = "frequencia/relatorio.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aluno = Aluno.objects.filter(user=self.request.user).first()
        context["aluno"] = aluno
        context["relatorio"] = calcular_frequencia(aluno) if aluno else []
        return context
