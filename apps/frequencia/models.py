from django.db import models

from apps.alunos.models import Aluno
from apps.core.models import TimestampedModel
from apps.escola.models import Disciplina, Turma
from apps.professores.models import Professor

from .managers import AulaQuerySet, PresencaAlunoQuerySet


class Aula(TimestampedModel):
    turma = models.ForeignKey(Turma, verbose_name="turma", on_delete=models.CASCADE, related_name="aulas")
    disciplina = models.ForeignKey(
        Disciplina, verbose_name="disciplina", on_delete=models.CASCADE, related_name="aulas"
    )
    professor = models.ForeignKey(
        Professor, verbose_name="professor", on_delete=models.PROTECT, related_name="aulas"
    )
    data = models.DateField("data")
    conteudo_ministrado = models.CharField("conteúdo ministrado", max_length=255, blank=True)

    objects = AulaQuerySet.as_manager()

    class Meta:
        verbose_name = "aula"
        verbose_name_plural = "aulas"
        unique_together = ("turma", "disciplina", "data")
        ordering = ["-data"]

    def __str__(self):
        return f"{self.turma} — {self.disciplina} — {self.data}"


class PresencaAluno(TimestampedModel):
    class Status(models.TextChoices):
        PRESENTE = "PRESENTE", "Presente"
        FALTA = "FALTA", "Falta"
        FALTA_JUSTIFICADA = "FALTA_JUSTIFICADA", "Falta justificada"

    aula = models.ForeignKey(Aula, verbose_name="aula", on_delete=models.CASCADE, related_name="presencas")
    aluno = models.ForeignKey(Aluno, verbose_name="aluno", on_delete=models.CASCADE, related_name="presencas")
    status = models.CharField("status", max_length=20, choices=Status.choices, default=Status.PRESENTE)
    observacao = models.CharField("observação", max_length=255, blank=True)

    objects = PresencaAlunoQuerySet.as_manager()

    class Meta:
        verbose_name = "presença"
        verbose_name_plural = "presenças"
        unique_together = ("aula", "aluno")

    def __str__(self):
        return f"{self.aluno} — {self.aula}: {self.get_status_display()}"
