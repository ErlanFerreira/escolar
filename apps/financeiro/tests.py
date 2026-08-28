from datetime import date
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.models import CustomUser
from apps.alunos.models import Aluno, AlunoResponsavel, Matricula, Responsavel
from apps.escola.models import AnoLetivo, Serie, Turma
from apps.financeiro.models import Cobranca, Pagamento, PlanoPagamento
from apps.financeiro.services import gerar_cobrancas_para_plano


@pytest.fixture
def ano_letivo(db):
    # data_inicio/data_fim como `date` de verdade: gerar_cobrancas_para_plano faz
    # aritmética de datas em cima de ano_letivo.data_inicio, então precisa ser um
    # objeto date, não a string usada nos outros apps (que nunca chamam métodos de date nela).
    return AnoLetivo.objects.create(
        ano=2026, data_inicio=date(2026, 2, 2), data_fim=date(2026, 12, 18), ativo=True
    )


@pytest.fixture
def serie(db):
    return Serie.objects.create(nome="3º ano", segmento=Serie.Segmento.FUNDAMENTAL_I, ordem=3)


@pytest.fixture
def turma(db, ano_letivo, serie):
    return Turma.objects.create(ano_letivo=ano_letivo, serie=serie, nome="A", turno=Turma.Turno.MANHA)


@pytest.fixture
def plano(db, ano_letivo):
    return PlanoPagamento.objects.create(
        nome="Mensalidade 2026",
        ano_letivo=ano_letivo,
        valor_mensalidade=Decimal("800.00"),
        dia_vencimento=10,
        numero_parcelas=3,
    )


@pytest.fixture
def responsavel(db):
    return Responsavel.objects.create(
        nome_completo="Responsável Financeiro", cpf="123.456.789-00", telefone="81911112222"
    )


@pytest.fixture
def aluno_matriculado(db, turma, ano_letivo, responsavel):
    aluno = Aluno.objects.create(
        nome_completo="Rafael Teste",
        data_nascimento="2017-01-01",
        matricula_numero="20260030",
        data_matricula_inicial="2026-02-02",
    )
    Matricula.objects.create(aluno=aluno, turma=turma, ano_letivo=ano_letivo, data_matricula="2026-02-02")
    AlunoResponsavel.objects.create(
        aluno=aluno,
        responsavel=responsavel,
        parentesco=AlunoResponsavel.Parentesco.MAE,
        responsavel_financeiro=True,
    )
    return aluno


@pytest.mark.django_db
class TestGerarCobrancasParaPlano:
    def test_gera_uma_cobranca_por_parcela_por_aluno_matriculado(self, plano, aluno_matriculado, responsavel):
        criadas = gerar_cobrancas_para_plano(plano)

        assert criadas == 3
        cobrancas = Cobranca.objects.filter(aluno=aluno_matriculado).order_by("competencia")
        assert list(cobrancas.values_list("competencia", flat=True)) == ["2026-02", "2026-03", "2026-04"]
        assert cobrancas.first().responsavel_financeiro == responsavel
        assert cobrancas.first().valor_final == Decimal("800.00")
        assert cobrancas.first().data_vencimento == date(2026, 2, 10)

    def test_rodar_de_novo_nao_duplica_cobrancas(self, plano, aluno_matriculado):
        gerar_cobrancas_para_plano(plano)
        criadas_na_segunda_vez = gerar_cobrancas_para_plano(plano)

        assert criadas_na_segunda_vez == 0
        assert Cobranca.objects.filter(aluno=aluno_matriculado).count() == 3

    def test_matricula_inativa_nao_gera_cobranca(self, plano, turma, ano_letivo):
        aluno = Aluno.objects.create(
            nome_completo="Sem Matrícula Ativa",
            data_nascimento="2017-01-01",
            matricula_numero="20260031",
            data_matricula_inicial="2026-02-02",
        )
        Matricula.objects.create(
            aluno=aluno,
            turma=turma,
            ano_letivo=ano_letivo,
            data_matricula="2026-02-02",
            status=Matricula.Status.CANCELADA,
        )

        gerar_cobrancas_para_plano(plano)

        assert not Cobranca.objects.filter(aluno=aluno).exists()


@pytest.mark.django_db
class TestStatusAtual:
    def test_pendente_vencida_aparece_como_atrasada(self, plano, aluno_matriculado):
        cobranca = Cobranca.objects.create(
            aluno=aluno_matriculado,
            plano=plano,
            competencia="2020-01",
            valor_original=Decimal("800.00"),
            data_vencimento=date(2020, 1, 10),
        )

        assert cobranca.status_atual == Cobranca.Status.ATRASADO

    def test_pendente_futura_continua_pendente(self, plano, aluno_matriculado):
        cobranca = Cobranca.objects.create(
            aluno=aluno_matriculado,
            plano=plano,
            competencia="2030-01",
            valor_original=Decimal("800.00"),
            data_vencimento=date(2030, 1, 10),
        )

        assert cobranca.status_atual == Cobranca.Status.PENDENTE

    def test_registrar_pagamento_marca_cobranca_como_paga(self, plano, aluno_matriculado):
        secretaria = CustomUser.objects.create_user(
            email="sec.fin@escola.test", password="senha-forte-123", role=CustomUser.Role.SECRETARIA
        )
        cobranca = Cobranca.objects.create(
            aluno=aluno_matriculado,
            plano=plano,
            competencia="2020-01",
            valor_original=Decimal("800.00"),
            data_vencimento=date(2020, 1, 10),
        )

        Pagamento.objects.create(
            cobranca=cobranca,
            valor_pago=Decimal("800.00"),
            data_pagamento=date(2020, 1, 8),
            forma_pagamento=Pagamento.FormaPagamento.PIX,
            registrado_por=secretaria,
        )

        cobranca.refresh_from_db()
        assert cobranca.status == Cobranca.Status.PAGO
        assert cobranca.status_atual == Cobranca.Status.PAGO
        assert cobranca.data_pagamento == date(2020, 1, 8)


@pytest.mark.django_db
class TestFinanceiroForUser:
    def test_responsavel_ve_apenas_as_proprias_cobrancas(self, plano, aluno_matriculado, responsavel):
        outro_aluno = Aluno.objects.create(
            nome_completo="Outro Aluno Financeiro",
            data_nascimento="2017-01-01",
            matricula_numero="20260032",
            data_matricula_inicial="2026-02-02",
        )
        Cobranca.objects.create(
            aluno=aluno_matriculado,
            plano=plano,
            competencia="2026-05",
            valor_original=Decimal("800.00"),
            data_vencimento=date(2026, 5, 10),
            responsavel_financeiro=responsavel,
        )
        Cobranca.objects.create(
            aluno=outro_aluno,
            plano=plano,
            competencia="2026-05",
            valor_original=Decimal("800.00"),
            data_vencimento=date(2026, 5, 10),
        )

        resp_user = CustomUser.objects.create_user(
            email="resp.fin@escola.test", password="senha-forte-123", role=CustomUser.Role.RESPONSAVEL
        )
        responsavel.user = resp_user
        responsavel.save()

        assert set(Cobranca.objects.for_user(resp_user)) == set(
            Cobranca.objects.filter(aluno=aluno_matriculado)
        )

    def test_responsavel_acessa_pagina_de_minhas_cobrancas(
        self, client, plano, aluno_matriculado, responsavel
    ):
        Cobranca.objects.create(
            aluno=aluno_matriculado,
            plano=plano,
            competencia="2026-05",
            valor_original=Decimal("800.00"),
            data_vencimento=date(2026, 5, 10),
            responsavel_financeiro=responsavel,
        )
        resp_user = CustomUser.objects.create_user(
            email="resp.fin2@escola.test", password="senha-forte-123", role=CustomUser.Role.RESPONSAVEL
        )
        responsavel.user = resp_user
        responsavel.save()

        client.login(username="resp.fin2@escola.test", password="senha-forte-123")
        response = client.get(reverse("financeiro:minhas_cobrancas"))

        assert response.status_code == 200
        assert "2026-05" in response.content.decode()

    def test_professor_nao_acessa_financeiro_da_secretaria(self, client):
        CustomUser.objects.create_user(
            email="prof.fin@escola.test", password="senha-forte-123", role=CustomUser.Role.PROFESSOR
        )
        client.login(username="prof.fin@escola.test", password="senha-forte-123")

        response = client.get(reverse("financeiro:lista"))

        assert response.status_code == 403


@pytest.mark.django_db
class TestGerarCobrancasView:
    def test_secretaria_gera_cobrancas_pela_tela(self, client, plano, aluno_matriculado):
        secretaria = CustomUser.objects.create_user(
            email="sec.gera@escola.test", password="senha-forte-123", role=CustomUser.Role.SECRETARIA
        )
        client.login(username=secretaria.email, password="senha-forte-123")

        response = client.post(reverse("financeiro:gerar"), {"plano": plano.pk})

        assert response.status_code == 302
        assert Cobranca.objects.filter(aluno=aluno_matriculado).count() == 3
