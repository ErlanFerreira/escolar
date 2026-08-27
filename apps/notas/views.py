from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, TemplateView

from apps.accounts.models import CustomUser
from apps.alunos.models import Aluno, Matricula
from apps.core.mixins import RoleRequiredMixin
from apps.escola.models import Turma
from apps.professores.models import Professor, ProfessorDisciplinaTurma

from .boletim import montar_boletim
from .forms import AvaliacaoForm, NotaFormSet
from .models import Avaliacao, Nota


class TurmaNotasView(RoleRequiredMixin, TemplateView):
    allowed_roles = (CustomUser.Role.PROFESSOR,)
    template_name = "notas/turma_notas.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        turma = get_object_or_404(Turma.objects.for_user(self.request.user), pk=kwargs["turma_id"])
        atribuicoes = ProfessorDisciplinaTurma.objects.filter(
            professor__user=self.request.user, turma=turma
        ).select_related("disciplina")
        avaliacoes_por_disciplina = [
            (
                atribuicao.disciplina,
                Avaliacao.objects.filter(
                    turma=turma, disciplina=atribuicao.disciplina, professor__user=self.request.user
                ),
            )
            for atribuicao in atribuicoes
        ]
        context["turma"] = turma
        context["avaliacoes_por_disciplina"] = avaliacoes_por_disciplina
        return context


class AvaliacaoCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (CustomUser.Role.PROFESSOR,)
    model = Avaliacao
    form_class = AvaliacaoForm
    template_name = "notas/avaliacao_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.turma = get_object_or_404(Turma.objects.for_user(request.user), pk=kwargs["turma_id"])
        # 404 (em vez de 403) se o professor não lecionar essa disciplina nessa turma —
        # não revela se a atribuição existe para outro professor.
        get_object_or_404(
            ProfessorDisciplinaTurma,
            professor__user=request.user,
            turma=self.turma,
            disciplina_id=kwargs["disciplina_id"],
        )
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["ano_letivo"] = self.turma.ano_letivo
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["turma"] = self.turma
        return context

    def form_valid(self, form):
        form.instance.turma = self.turma
        form.instance.disciplina_id = self.kwargs["disciplina_id"]
        form.instance.professor = Professor.objects.get(user=self.request.user)
        response = super().form_valid(form)

        alunos_ids = Matricula.objects.filter(
            turma=self.turma, ano_letivo=self.turma.ano_letivo, status=Matricula.Status.ATIVA
        ).values_list("aluno_id", flat=True)
        Nota.objects.bulk_create([Nota(avaliacao=self.object, aluno_id=aluno_id) for aluno_id in alunos_ids])

        return response

    def get_success_url(self):
        return reverse("notas:lancar", args=[self.object.pk])


class LancarNotasView(RoleRequiredMixin, TemplateView):
    allowed_roles = (CustomUser.Role.PROFESSOR,)
    template_name = "notas/lancar_notas.html"

    def dispatch(self, request, *args, **kwargs):
        self.avaliacao = get_object_or_404(
            Avaliacao.objects.for_user(request.user), pk=kwargs["avaliacao_id"]
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        formset = NotaFormSet(queryset=self._queryset())
        return self.render_to_response(self.get_context_data(formset=formset))

    def post(self, request, *args, **kwargs):
        formset = NotaFormSet(request.POST, queryset=self._queryset())
        if formset.is_valid():
            formset.save()
            messages.success(request, "Notas salvas com sucesso.")
            return redirect("notas:turma", turma_id=self.avaliacao.turma_id)
        return self.render_to_response(self.get_context_data(formset=formset))

    def _queryset(self):
        return (
            Nota.objects.filter(avaliacao=self.avaliacao)
            .select_related("aluno")
            .order_by("aluno__nome_completo")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["avaliacao"] = self.avaliacao
        return context


class BoletimAlunoView(RoleRequiredMixin, TemplateView):
    allowed_roles = (CustomUser.Role.SECRETARIA, CustomUser.Role.DIRETOR, CustomUser.Role.RESPONSAVEL)
    template_name = "notas/boletim.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aluno = get_object_or_404(Aluno.objects.for_user(self.request.user), pk=kwargs["aluno_id"])
        context["aluno"] = aluno
        context["boletim"] = montar_boletim(aluno)
        return context


class MeuBoletimView(RoleRequiredMixin, TemplateView):
    allowed_roles = (CustomUser.Role.ALUNO,)
    template_name = "notas/boletim.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        aluno = Aluno.objects.filter(user=self.request.user).first()
        context["aluno"] = aluno
        context["boletim"] = montar_boletim(aluno) if aluno else []
        return context
