from datetime import date

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.accounts.models import CustomUser
from apps.alunos.models import Aluno, Responsavel
from apps.core.models import TimestampedModel
from apps.escola.models import AnoLetivo

from .managers import CobrancaQuerySet


class PlanoPagamento(TimestampedModel):
    nome = models.CharField("nome", max_length=100)
    ano_letivo = models.ForeignKey(
        AnoLetivo, verbose_name="ano letivo", on_delete=models.CASCADE, related_name="planos_pagamento"
    )
    valor_mensalidade = models.DecimalField("valor da mensalidade", max_digits=10, decimal_places=2)
    dia_vencimento = models.PositiveSmallIntegerField(
        "dia de vencimento", validators=[MinValueValidator(1), MaxValueValidator(28)]
    )
    numero_parcelas = models.PositiveSmallIntegerField("número de parcelas", default=12)
    taxa_multa_atraso = models.DecimalField(
        "taxa de multa por atraso (%)", max_digits=5, decimal_places=2, default=0
    )
    taxa_juros_diaria = models.DecimalField(
        "taxa de juros diária (%)", max_digits=5, decimal_places=2, default=0
    )

    class Meta:
        verbose_name = "plano de pagamento"
        verbose_name_plural = "planos de pagamento"

    def __str__(self):
        return f"{self.nome} ({self.ano_letivo})"


class Cobranca(TimestampedModel):
    class Status(models.TextChoices):
        PENDENTE = "PENDENTE", "Pendente"
        PAGO = "PAGO", "Pago"
        ATRASADO = "ATRASADO", "Atrasado"
        CANCELADO = "CANCELADO", "Cancelado"
        ISENTO = "ISENTO", "Isento"

    aluno = models.ForeignKey(Aluno, verbose_name="aluno", on_delete=models.CASCADE, related_name="cobrancas")
    plano = models.ForeignKey(
        PlanoPagamento, verbose_name="plano de pagamento", on_delete=models.PROTECT, related_name="cobrancas"
    )
    responsavel_financeiro = models.ForeignKey(
        Responsavel,
        verbose_name="responsável financeiro",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cobrancas",
    )
    competencia = models.CharField("competência", max_length=7, help_text="Ex: 2026-03")
    valor_original = models.DecimalField("valor original", max_digits=10, decimal_places=2)
    valor_desconto = models.DecimalField("desconto", max_digits=10, decimal_places=2, default=0)
    valor_final = models.DecimalField("valor final", max_digits=10, decimal_places=2)
    data_vencimento = models.DateField("data de vencimento")
    status = models.CharField("status", max_length=20, choices=Status.choices, default=Status.PENDENTE)
    data_pagamento = models.DateField("data de pagamento", null=True, blank=True)

    objects = CobrancaQuerySet.as_manager()

    class Meta:
        verbose_name = "cobrança"
        verbose_name_plural = "cobranças"
        unique_together = ("aluno", "plano", "competencia")
        ordering = ["-data_vencimento"]

    def __str__(self):
        return f"{self.aluno} — {self.competencia} — {self.get_status_display()}"

    def save(self, *args, **kwargs):
        if self.valor_final is None:
            self.valor_final = self.valor_original - self.valor_desconto
        super().save(*args, **kwargs)

    @property
    def status_atual(self):
        """Status "de verdade" no momento da consulta — ATRASADO é sempre calculado,
        nunca persistido por um job agendado (mantém o MVP sem dependência de cron/Celery)."""
        if self.status == self.Status.PENDENTE and self.data_vencimento < date.today():
            return self.Status.ATRASADO
        return self.status

    def get_status_atual_display(self):
        return dict(self.Status.choices)[self.status_atual]


class Pagamento(TimestampedModel):
    class FormaPagamento(models.TextChoices):
        DINHEIRO = "DINHEIRO", "Dinheiro"
        PIX = "PIX", "PIX"
        BOLETO = "BOLETO", "Boleto"
        CARTAO = "CARTAO", "Cartão"
        TRANSFERENCIA = "TRANSFERENCIA", "Transferência"

    cobranca = models.OneToOneField(
        Cobranca, verbose_name="cobrança", on_delete=models.CASCADE, related_name="pagamento"
    )
    valor_pago = models.DecimalField("valor pago", max_digits=10, decimal_places=2)
    data_pagamento = models.DateField("data de pagamento")
    forma_pagamento = models.CharField("forma de pagamento", max_length=20, choices=FormaPagamento.choices)
    registrado_por = models.ForeignKey(
        CustomUser,
        verbose_name="registrado por",
        on_delete=models.PROTECT,
        related_name="pagamentos_registrados",
    )
    observacao = models.CharField("observação", max_length=255, blank=True)

    class Meta:
        verbose_name = "pagamento"
        verbose_name_plural = "pagamentos"

    def __str__(self):
        return f"Pagamento de {self.cobranca}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        Cobranca.objects.filter(pk=self.cobranca_id).update(
            status=Cobranca.Status.PAGO, data_pagamento=self.data_pagamento
        )
