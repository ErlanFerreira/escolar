from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views.generic import DetailView, ListView
from formtools.wizard.views import SessionWizardView

from apps.accounts.models import CustomUser
from apps.core.mixins import RoleRequiredMixin

from .forms import AlunoForm, MatriculaTurmaForm, ResponsavelFormSet
from .models import Aluno, AlunoResponsavel, Matricula, Responsavel

FORMS = [
    ("aluno", AlunoForm),
    ("responsaveis", ResponsavelFormSet),
    ("turma", MatriculaTurmaForm),
]

TEMPLATES = {
    "aluno": "alunos/matricula_wizard_aluno.html",
    "responsaveis": "alunos/matricula_wizard_responsaveis.html",
    "turma": "alunos/matricula_wizard_turma.html",
}


def gerar_numero_matricula(ano_letivo):
    prefixo = str(ano_letivo.ano)
    sequencia = Aluno.objects.filter(matricula_numero__startswith=prefixo).count() + 1
    while True:
        numero = f"{prefixo}{sequencia:04d}"
        if not Aluno.objects.filter(matricula_numero=numero).exists():
            return numero
        sequencia += 1


class MatriculaWizardView(RoleRequiredMixin, SessionWizardView):
    allowed_roles = (CustomUser.Role.SECRETARIA, CustomUser.Role.DIRETOR)
    form_list = FORMS

    def get_template_names(self):
        return [TEMPLATES[self.steps.current]]

    def done(self, form_list, form_dict, **kwargs):
        aluno_form = form_dict["aluno"]
        responsaveis_formset = form_dict["responsaveis"]
        turma = form_dict["turma"].cleaned_data["turma"]
        ano_letivo = turma.ano_letivo
        hoje = timezone.localdate()

        with transaction.atomic():
            aluno = aluno_form.save(commit=False)
            aluno.matricula_numero = gerar_numero_matricula(ano_letivo)
            aluno.data_matricula_inicial = hoje
            aluno.save()

            for form in responsaveis_formset:
                data = form.cleaned_data
                if not data.get("nome_completo"):
                    continue
                responsavel, _ = Responsavel.objects.get_or_create(
                    cpf=data["cpf"],
                    defaults={
                        "nome_completo": data["nome_completo"],
                        "telefone": data["telefone"],
                        "telefone_secundario": data.get("telefone_secundario", ""),
                        "email": data.get("email", ""),
                        "endereco": data.get("endereco", ""),
                        "profissao": data.get("profissao", ""),
                    },
                )
                AlunoResponsavel.objects.create(
                    aluno=aluno,
                    responsavel=responsavel,
                    parentesco=data["parentesco"],
                    responsavel_financeiro=data.get("responsavel_financeiro", False),
                    responsavel_pedagogico=data.get("responsavel_pedagogico", False),
                    reside_com_aluno=data.get("reside_com_aluno", False),
                )

            Matricula.objects.create(
                aluno=aluno,
                turma=turma,
                ano_letivo=ano_letivo,
                data_matricula=hoje,
            )

        messages.success(self.request, f"Matrícula de {aluno.nome_completo} concluída com sucesso.")
        return redirect(reverse("alunos:detalhe", args=[aluno.pk]))


class AlunoListView(RoleRequiredMixin, ListView):
    allowed_roles = (CustomUser.Role.SECRETARIA, CustomUser.Role.DIRETOR)
    model = Aluno
    template_name = "alunos/lista.html"
    context_object_name = "alunos"
    paginate_by = 25

    def get_queryset(self):
        return Aluno.objects.for_user(self.request.user).prefetch_related("matriculas__turma")


class AlunoDetailView(RoleRequiredMixin, DetailView):
    # Visões próprias para professor/responsável/aluno chegam no M9 (dashboard por perfil).
    allowed_roles = (CustomUser.Role.SECRETARIA, CustomUser.Role.DIRETOR)
    model = Aluno
    template_name = "alunos/detalhe.html"
    context_object_name = "aluno"

    def get_queryset(self):
        return Aluno.objects.for_user(self.request.user).prefetch_related(
            "matriculas__turma", "responsaveis__responsavel"
        )
