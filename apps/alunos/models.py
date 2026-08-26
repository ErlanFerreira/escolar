from django.db import models

from apps.accounts.models import CustomUser
from apps.core.models import TimestampedModel
from apps.escola.models import AnoLetivo, Turma

from .managers import AlunoQuerySet, MatriculaQuerySet


class Aluno(TimestampedModel):
    class Sexo(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMININO = "F", "Feminino"

    user = models.OneToOneField(
        CustomUser,
        verbose_name="usuário",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="aluno",
    )
    nome_completo = models.CharField("nome completo", max_length=255)
    data_nascimento = models.DateField("data de nascimento")
    cpf = models.CharField("CPF", max_length=14, unique=True, null=True, blank=True)
    rg = models.CharField("RG", max_length=20, blank=True)
    sexo = models.CharField("sexo", max_length=1, choices=Sexo.choices, blank=True)
    foto = models.ImageField("foto", upload_to="alunos/", null=True, blank=True)
    matricula_numero = models.CharField("número de matrícula", max_length=20, unique=True)
    data_matricula_inicial = models.DateField("data da matrícula inicial")
    ativo = models.BooleanField("ativo", default=True)
    observacoes = models.TextField(
        "observações", blank=True, help_text="Necessidades especiais, alergias, etc."
    )

    objects = AlunoQuerySet.as_manager()

    class Meta:
        verbose_name = "aluno"
        verbose_name_plural = "alunos"
        ordering = ["nome_completo"]

    def __str__(self):
        return self.nome_completo


class Responsavel(TimestampedModel):
    user = models.OneToOneField(
        CustomUser,
        verbose_name="usuário",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="responsavel",
    )
    nome_completo = models.CharField("nome completo", max_length=255)
    cpf = models.CharField("CPF", max_length=14, unique=True)
    telefone = models.CharField("telefone", max_length=20)
    telefone_secundario = models.CharField("telefone secundário", max_length=20, blank=True)
    email = models.EmailField("e-mail", blank=True)
    endereco = models.CharField("endereço", max_length=255, blank=True)
    profissao = models.CharField("profissão", max_length=100, blank=True)

    class Meta:
        verbose_name = "responsável"
        verbose_name_plural = "responsáveis"
        ordering = ["nome_completo"]

    def __str__(self):
        return self.nome_completo


class AlunoResponsavel(TimestampedModel):
    class Parentesco(models.TextChoices):
        PAI = "PAI", "Pai"
        MAE = "MAE", "Mãe"
        AVO = "AVO", "Avô/Avó"
        TUTOR = "TUTOR", "Tutor(a)"
        OUTRO = "OUTRO", "Outro"

    aluno = models.ForeignKey(
        Aluno, verbose_name="aluno", on_delete=models.CASCADE, related_name="responsaveis"
    )
    responsavel = models.ForeignKey(
        Responsavel, verbose_name="responsável", on_delete=models.CASCADE, related_name="alunos"
    )
    parentesco = models.CharField("parentesco", max_length=10, choices=Parentesco.choices)
    responsavel_financeiro = models.BooleanField("responsável financeiro", default=False)
    responsavel_pedagogico = models.BooleanField(
        "responsável pedagógico", default=True, help_text="Recebe comunicados sobre o aluno"
    )
    reside_com_aluno = models.BooleanField("reside com o aluno", default=True)

    class Meta:
        verbose_name = "vínculo aluno-responsável"
        verbose_name_plural = "vínculos aluno-responsável"
        unique_together = ("aluno", "responsavel")

    def __str__(self):
        return f"{self.responsavel} ({self.get_parentesco_display()}) de {self.aluno}"


class Matricula(TimestampedModel):
    class Status(models.TextChoices):
        ATIVA = "ATIVA", "Ativa"
        TRANCADA = "TRANCADA", "Trancada"
        TRANSFERIDA = "TRANSFERIDA", "Transferida"
        CANCELADA = "CANCELADA", "Cancelada"
        CONCLUIDA = "CONCLUIDA", "Concluída"

    aluno = models.ForeignKey(
        Aluno, verbose_name="aluno", on_delete=models.CASCADE, related_name="matriculas"
    )
    turma = models.ForeignKey(
        Turma, verbose_name="turma", on_delete=models.PROTECT, related_name="matriculas"
    )
    ano_letivo = models.ForeignKey(
        AnoLetivo, verbose_name="ano letivo", on_delete=models.PROTECT, related_name="matriculas"
    )
    data_matricula = models.DateField("data da matrícula")
    status = models.CharField("status", max_length=20, choices=Status.choices, default=Status.ATIVA)
    data_cancelamento = models.DateField("data de cancelamento", null=True, blank=True)

    objects = MatriculaQuerySet.as_manager()

    class Meta:
        verbose_name = "matrícula"
        verbose_name_plural = "matrículas"
        unique_together = ("aluno", "ano_letivo")
        ordering = ["-ano_letivo", "aluno__nome_completo"]

    def __str__(self):
        return f"{self.aluno} — {self.turma} ({self.ano_letivo})"
