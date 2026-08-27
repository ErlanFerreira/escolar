from django.db import models

from apps.alunos.models import Aluno
from apps.core.models import TimestampedModel
from apps.escola.models import AnoLetivo, Disciplina, Turma
from apps.professores.models import Professor

from .managers import AvaliacaoQuerySet, NotaQuerySet


class TipoAvaliacao(TimestampedModel):
    nome = models.CharField("nome", max_length=100)
    peso = models.DecimalField("peso", max_digits=4, decimal_places=2, default=1)

    class Meta:
        verbose_name = "tipo de avaliação"
        verbose_name_plural = "tipos de avaliação"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class PeriodoLetivo(TimestampedModel):
    ano_letivo = models.ForeignKey(
        AnoLetivo, verbose_name="ano letivo", on_delete=models.CASCADE, related_name="periodos"
    )
    numero = models.PositiveSmallIntegerField("número")
    nome = models.CharField("nome", max_length=50, help_text="Ex: 1º Bimestre")
    data_inicio = models.DateField("data de início")
    data_fim = models.DateField("data de término")

    class Meta:
        verbose_name = "período letivo"
        verbose_name_plural = "períodos letivos"
        unique_together = ("ano_letivo", "numero")
        ordering = ["ano_letivo", "numero"]

    def __str__(self):
        return f"{self.nome} ({self.ano_letivo})"


class Avaliacao(TimestampedModel):
    turma = models.ForeignKey(
        Turma, verbose_name="turma", on_delete=models.CASCADE, related_name="avaliacoes"
    )
    disciplina = models.ForeignKey(
        Disciplina, verbose_name="disciplina", on_delete=models.CASCADE, related_name="avaliacoes"
    )
    professor = models.ForeignKey(
        Professor, verbose_name="professor", on_delete=models.PROTECT, related_name="avaliacoes"
    )
    periodo = models.ForeignKey(
        PeriodoLetivo, verbose_name="período letivo", on_delete=models.CASCADE, related_name="avaliacoes"
    )
    tipo = models.ForeignKey(
        TipoAvaliacao, verbose_name="tipo", on_delete=models.PROTECT, related_name="avaliacoes"
    )
    titulo = models.CharField("título", max_length=255)
    data = models.DateField("data")
    valor_maximo = models.DecimalField("valor máximo", max_digits=5, decimal_places=2, default=10)
    peso = models.DecimalField("peso", max_digits=4, decimal_places=2, default=1)

    objects = AvaliacaoQuerySet.as_manager()

    class Meta:
        verbose_name = "avaliação"
        verbose_name_plural = "avaliações"
        ordering = ["-data"]

    def __str__(self):
        return f"{self.titulo} — {self.turma} — {self.disciplina}"


class Nota(TimestampedModel):
    avaliacao = models.ForeignKey(
        Avaliacao, verbose_name="avaliação", on_delete=models.CASCADE, related_name="notas"
    )
    aluno = models.ForeignKey(Aluno, verbose_name="aluno", on_delete=models.CASCADE, related_name="notas")
    valor = models.DecimalField("valor", max_digits=5, decimal_places=2, null=True, blank=True)
    observacao = models.CharField("observação", max_length=255, blank=True)

    objects = NotaQuerySet.as_manager()

    class Meta:
        verbose_name = "nota"
        verbose_name_plural = "notas"
        unique_together = ("avaliacao", "aluno")

    def __str__(self):
        valor = self.valor if self.valor is not None else "—"
        return f"{self.aluno} — {self.avaliacao}: {valor}"
