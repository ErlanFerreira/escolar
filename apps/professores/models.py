from django.db import models

from apps.accounts.models import CustomUser
from apps.core.models import TimestampedModel
from apps.escola.models import AnoLetivo, Disciplina, Turma


class Professor(TimestampedModel):
    user = models.OneToOneField(
        CustomUser, verbose_name="usuário", on_delete=models.CASCADE, related_name="professor"
    )
    cpf = models.CharField("CPF", max_length=14, unique=True, null=True, blank=True)
    data_nascimento = models.DateField("data de nascimento", null=True, blank=True)
    formacao = models.CharField("formação", max_length=255, blank=True)
    disciplinas = models.ManyToManyField(
        Disciplina, verbose_name="disciplinas", related_name="professores", blank=True
    )
    ativo = models.BooleanField("ativo", default=True)

    class Meta:
        verbose_name = "professor"
        verbose_name_plural = "professores"

    def __str__(self):
        return self.user.get_full_name() or self.user.email


class ProfessorDisciplinaTurma(TimestampedModel):
    professor = models.ForeignKey(
        Professor, verbose_name="professor", on_delete=models.CASCADE, related_name="atribuicoes"
    )
    turma = models.ForeignKey(
        Turma, verbose_name="turma", on_delete=models.CASCADE, related_name="atribuicoes"
    )
    disciplina = models.ForeignKey(
        Disciplina, verbose_name="disciplina", on_delete=models.CASCADE, related_name="atribuicoes"
    )
    ano_letivo = models.ForeignKey(
        AnoLetivo, verbose_name="ano letivo", on_delete=models.CASCADE, related_name="atribuicoes"
    )

    class Meta:
        verbose_name = "atribuição"
        verbose_name_plural = "atribuições"
        unique_together = ("turma", "disciplina", "ano_letivo")

    def __str__(self):
        return f"{self.professor} — {self.disciplina} — {self.turma}"
