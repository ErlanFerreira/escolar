from django.core.exceptions import ValidationError
from django.db import models
from solo.models import SingletonModel

from apps.core.models import TimestampedModel

from .managers import TurmaQuerySet


class Escola(SingletonModel):
    """Dados institucionais únicos da escola (v1 = uma única escola).

    Extensão futura para múltiplas escolas: adicionar FK ``escola`` em
    ``AnoLetivo`` e filtrar a partir dali — o restante da hierarquia
    (Aluno, Nota, Cobranca...) já herda isso transitivamente via Turma/AnoLetivo.
    """

    nome = models.CharField("nome", max_length=255)
    cnpj = models.CharField("CNPJ", max_length=18, blank=True)
    endereco = models.CharField("endereço", max_length=255, blank=True)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    email = models.EmailField("e-mail", blank=True)
    logo = models.ImageField("logo", upload_to="escola/", null=True, blank=True)
    diretor_nome = models.CharField("nome do(a) diretor(a)", max_length=255, blank=True)

    class Meta:
        verbose_name = "escola"
        verbose_name_plural = "escola"

    def __str__(self):
        return self.nome or "Escola"


class AnoLetivo(TimestampedModel):
    class Status(models.TextChoices):
        PLANEJAMENTO = "PLANEJAMENTO", "Planejamento"
        EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
        ENCERRADO = "ENCERRADO", "Encerrado"

    ano = models.PositiveIntegerField("ano", unique=True)
    data_inicio = models.DateField("data de início")
    data_fim = models.DateField("data de término")
    status = models.CharField("status", max_length=20, choices=Status.choices, default=Status.PLANEJAMENTO)
    ativo = models.BooleanField("ativo", default=False)

    class Meta:
        verbose_name = "ano letivo"
        verbose_name_plural = "anos letivos"
        ordering = ["-ano"]

    def __str__(self):
        return str(self.ano)

    def clean(self):
        if self.ativo:
            qs = AnoLetivo.objects.filter(ativo=True).exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("Já existe um ano letivo ativo. Desative-o antes de ativar outro.")
        if self.data_fim <= self.data_inicio:
            raise ValidationError("A data de término deve ser posterior à data de início.")


class Serie(TimestampedModel):
    class Segmento(models.TextChoices):
        INFANTIL = "INFANTIL", "Educação Infantil"
        FUNDAMENTAL_I = "FUNDAMENTAL_I", "Fundamental I"
        FUNDAMENTAL_II = "FUNDAMENTAL_II", "Fundamental II"
        MEDIO = "MEDIO", "Ensino Médio"

    nome = models.CharField("nome", max_length=100)
    segmento = models.CharField("segmento", max_length=20, choices=Segmento.choices)
    ordem = models.PositiveSmallIntegerField("ordem", default=0)

    class Meta:
        verbose_name = "série"
        verbose_name_plural = "séries"
        ordering = ["ordem", "nome"]

    def __str__(self):
        return self.nome


class Turma(TimestampedModel):
    class Turno(models.TextChoices):
        MANHA = "MANHA", "Manhã"
        TARDE = "TARDE", "Tarde"
        NOITE = "NOITE", "Noite"
        INTEGRAL = "INTEGRAL", "Integral"

    ano_letivo = models.ForeignKey(
        AnoLetivo, verbose_name="ano letivo", on_delete=models.PROTECT, related_name="turmas"
    )
    serie = models.ForeignKey(Serie, verbose_name="série", on_delete=models.PROTECT, related_name="turmas")
    nome = models.CharField("nome", max_length=20, help_text="Ex: A, B, Único")
    turno = models.CharField("turno", max_length=20, choices=Turno.choices)
    capacidade_maxima = models.PositiveSmallIntegerField("capacidade máxima", default=30)
    sala = models.CharField("sala", max_length=50, blank=True)

    objects = TurmaQuerySet.as_manager()

    class Meta:
        verbose_name = "turma"
        verbose_name_plural = "turmas"
        unique_together = ("ano_letivo", "serie", "nome")
        ordering = ["ano_letivo", "serie__ordem", "nome"]

    def __str__(self):
        return f"{self.serie} {self.nome} ({self.ano_letivo})"


class Disciplina(TimestampedModel):
    nome = models.CharField("nome", max_length=100)
    codigo = models.CharField("código", max_length=20, unique=True)
    carga_horaria_semanal = models.PositiveSmallIntegerField("carga horária semanal", default=0)

    class Meta:
        verbose_name = "disciplina"
        verbose_name_plural = "disciplinas"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class MatrizCurricular(TimestampedModel):
    ano_letivo = models.ForeignKey(
        AnoLetivo, verbose_name="ano letivo", on_delete=models.CASCADE, related_name="matriz_curricular"
    )
    serie = models.ForeignKey(
        Serie, verbose_name="série", on_delete=models.CASCADE, related_name="matriz_curricular"
    )
    disciplina = models.ForeignKey(
        Disciplina, verbose_name="disciplina", on_delete=models.CASCADE, related_name="matriz_curricular"
    )
    carga_horaria_anual = models.PositiveSmallIntegerField("carga horária anual", default=0)

    class Meta:
        verbose_name = "item da matriz curricular"
        verbose_name_plural = "matriz curricular"
        unique_together = ("ano_letivo", "serie", "disciplina")

    def __str__(self):
        return f"{self.serie} — {self.disciplina} ({self.ano_letivo})"
