from django.core.management.base import BaseCommand, CommandError

from apps.financeiro.models import PlanoPagamento
from apps.financeiro.services import gerar_cobrancas_para_plano


class Command(BaseCommand):
    help = "Gera as cobranças mensais de um plano de pagamento para todas as matrículas ativas do ano letivo."

    def add_arguments(self, parser):
        parser.add_argument("plano_id", type=int)

    def handle(self, *args, **options):
        try:
            plano = PlanoPagamento.objects.get(pk=options["plano_id"])
        except PlanoPagamento.DoesNotExist as exc:
            raise CommandError(f"Plano de pagamento {options['plano_id']} não encontrado.") from exc

        criadas = gerar_cobrancas_para_plano(plano)
        self.stdout.write(self.style.SUCCESS(f"{criadas} cobrança(s) criada(s) para o plano '{plano}'."))
