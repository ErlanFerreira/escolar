import calendar
from datetime import date

from dateutil.relativedelta import relativedelta

from apps.alunos.models import AlunoResponsavel, Matricula

from .models import Cobranca


def gerar_cobrancas_para_plano(plano):
    """Gera uma Cobranca por matrícula ativa x parcela do plano, pulando as que já existem
    (idempotente via unique_together aluno+plano+competencia). Retorna quantas foram criadas."""
    matriculas = Matricula.objects.filter(
        ano_letivo=plano.ano_letivo, status=Matricula.Status.ATIVA
    ).select_related("aluno")

    inicio = plano.ano_letivo.data_inicio.replace(day=1)
    criadas = 0

    for matricula in matriculas:
        vinculo = (
            AlunoResponsavel.objects.filter(aluno=matricula.aluno, responsavel_financeiro=True)
            .select_related("responsavel")
            .first()
        )
        responsavel = vinculo.responsavel if vinculo else None

        for indice in range(plano.numero_parcelas):
            mes_referencia = inicio + relativedelta(months=indice)
            competencia = mes_referencia.strftime("%Y-%m")
            ultimo_dia_do_mes = calendar.monthrange(mes_referencia.year, mes_referencia.month)[1]
            dia_vencimento = min(plano.dia_vencimento, ultimo_dia_do_mes)
            vencimento = date(mes_referencia.year, mes_referencia.month, dia_vencimento)

            _, criada = Cobranca.objects.get_or_create(
                aluno=matricula.aluno,
                plano=plano,
                competencia=competencia,
                defaults={
                    "responsavel_financeiro": responsavel,
                    "valor_original": plano.valor_mensalidade,
                    "valor_final": plano.valor_mensalidade,
                    "data_vencimento": vencimento,
                },
            )
            if criada:
                criadas += 1

    return criadas
