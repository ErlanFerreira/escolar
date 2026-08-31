from django.db import models

from apps.accounts.models import CustomUser
from apps.core.models import TimestampedModel
from apps.escola.models import Turma

from .managers import ComunicadoQuerySet


class Comunicado(TimestampedModel):
    class PublicoAlvo(models.TextChoices):
        TODOS = "TODOS", "Todos"
        PROFESSORES = "PROFESSORES", "Professores"
        RESPONSAVEIS = "RESPONSAVEIS", "Responsáveis"
        TURMA_ESPECIFICA = "TURMA_ESPECIFICA", "Turma específica"

    titulo = models.CharField("título", max_length=255)
    corpo = models.TextField("mensagem")
    autor = models.ForeignKey(
        CustomUser, verbose_name="autor", on_delete=models.PROTECT, related_name="comunicados"
    )
    data_publicacao = models.DateTimeField("data de publicação", auto_now_add=True)
    turmas = models.ManyToManyField(
        Turma,
        verbose_name="turmas",
        blank=True,
        related_name="comunicados",
        help_text="Deixe em branco para não restringir por turma.",
    )
    publico_alvo = models.CharField(
        "público-alvo", max_length=20, choices=PublicoAlvo.choices, default=PublicoAlvo.TODOS
    )
    anexo = models.FileField("anexo", upload_to="comunicados/", null=True, blank=True)
    urgente = models.BooleanField("urgente", default=False)

    objects = ComunicadoQuerySet.as_manager()

    class Meta:
        verbose_name = "comunicado"
        verbose_name_plural = "comunicados"
        ordering = ["-data_publicacao"]

    def __str__(self):
        return self.titulo


class ComunicadoLeitura(TimestampedModel):
    comunicado = models.ForeignKey(
        Comunicado, verbose_name="comunicado", on_delete=models.CASCADE, related_name="leituras"
    )
    user = models.ForeignKey(
        CustomUser, verbose_name="usuário", on_delete=models.CASCADE, related_name="comunicados_lidos"
    )
    lida_em = models.DateTimeField("lida em", null=True, blank=True)

    class Meta:
        verbose_name = "leitura de comunicado"
        verbose_name_plural = "leituras de comunicado"
        unique_together = ("comunicado", "user")

    def __str__(self):
        status = "lido" if self.lida_em else "não lido"
        return f"{self.user} — {self.comunicado} ({status})"
