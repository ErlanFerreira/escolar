from datetime import date
from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.models import CustomUser
from apps.alunos.models import Aluno, AlunoResponsavel, Matricula, Responsavel
from apps.escola.models import AnoLetivo, Disciplina, Serie, Turma
from apps.financeiro.models import Cobranca, PlanoPagamento
from apps.frequencia.models import Aula, PresencaAluno
from apps.notas.models import Avaliacao, Nota, PeriodoLetivo, TipoAvaliacao
from apps.professores.models import Professor, ProfessorDisciplinaTurma


@pytest.fixture
def ano_letivo(db):
    return AnoLetivo.objects.create(
        ano=2026, data_inicio=date(2026, 2, 2), data_fim=date(2026, 12, 18), ativo=True
    )


@pytest.fixture
def serie(db):
    return Serie.objects.create(nome="7º ano", segmento=Serie.Segmento.FUNDAMENTAL_II, ordem=7)


@pytest.fixture
def turma(db, ano_letivo, serie):
    return Turma.objects.create(ano_letivo=ano_letivo, serie=serie, nome="A", turno=Turma.Turno.MANHA)


@pytest.fixture
def outra_turma(db, ano_letivo, serie):
    return Turma.objects.create(ano_letivo=ano_letivo, serie=serie, nome="B", turno=Turma.Turno.TARDE)


@pytest.mark.django_db
class TestSecretariaDashboard:
    def test_cards_mostram_totais_corretos(self, client, turma, outra_turma, ano_letivo):
        CustomUser.objects.create_user(
            email="sec.dash@escola.test", password="senha-forte-123", role=CustomUser.Role.SECRETARIA
        )
        aluno_ativo = Aluno.objects.create(
            nome_completo="Ativo",
            data_nascimento="2015-01-01",
            matricula_numero="D001",
            data_matricula_inicial="2026-02-02",
            ativo=True,
        )
        Aluno.objects.create(
            nome_completo="Inativo",
            data_nascimento="2015-01-01",
            matricula_numero="D002",
            data_matricula_inicial="2026-02-02",
            ativo=False,
        )
        plano = PlanoPagamento.objects.create(
            nome="Mensalidade", ano_letivo=ano_letivo, valor_mensalidade=Decimal("500.00"), dia_vencimento=10
        )
        Cobranca.objects.create(
            aluno=aluno_ativo,
            plano=plano,
            competencia="2020-01",
            valor_original=Decimal("500.00"),
            data_vencimento=date(2020, 1, 10),
        )

        client.login(username="sec.dash@escola.test", password="senha-forte-123")
        response = client.get(reverse("dashboard:secretaria"))

        assert response.status_code == 200
        assert response.context["total_alunos_ativos"] == 1
        assert response.context["total_turmas_ativas"] == 2
        assert response.context["total_cobrancas_atrasadas"] == 1
        assert response.context["valor_atrasado"] == Decimal("500.00")


@pytest.mark.django_db
class TestProfessorDashboard:
    def test_conta_apenas_as_proprias_turmas(self, client, turma, outra_turma, ano_letivo):
        disciplina = Disciplina.objects.create(nome="Geografia", codigo="GEO")
        user = CustomUser.objects.create_user(
            email="prof.dash@escola.test", password="senha-forte-123", role=CustomUser.Role.PROFESSOR
        )
        professor = Professor.objects.create(user=user)
        ProfessorDisciplinaTurma.objects.create(
            professor=professor, turma=turma, disciplina=disciplina, ano_letivo=ano_letivo
        )
        # outro professor leciona a outra turma — não deve contar aqui
        outro_user = CustomUser.objects.create_user(
            email="outro.dash@escola.test", password="senha-forte-123", role=CustomUser.Role.PROFESSOR
        )
        outro_professor = Professor.objects.create(user=outro_user)
        ProfessorDisciplinaTurma.objects.create(
            professor=outro_professor, turma=outra_turma, disciplina=disciplina, ano_letivo=ano_letivo
        )

        client.login(username="prof.dash@escola.test", password="senha-forte-123")
        response = client.get(reverse("dashboard:professor"))

        assert response.status_code == 200
        assert list(response.context["minhas_turmas"]) == [turma]


@pytest.mark.django_db
class TestResponsavelDashboard:
    def test_cobrancas_atrasadas_sao_apenas_as_do_proprio_responsavel(self, client, turma, ano_letivo):
        plano = PlanoPagamento.objects.create(
            nome="Mensalidade", ano_letivo=ano_letivo, valor_mensalidade=Decimal("500.00"), dia_vencimento=10
        )
        meu_filho = Aluno.objects.create(
            nome_completo="Meu Filho",
            data_nascimento="2015-01-01",
            matricula_numero="D010",
            data_matricula_inicial="2026-02-02",
        )
        filho_alheio = Aluno.objects.create(
            nome_completo="Filho Alheio",
            data_nascimento="2015-01-01",
            matricula_numero="D011",
            data_matricula_inicial="2026-02-02",
        )
        resp_user = CustomUser.objects.create_user(
            email="resp.dash@escola.test", password="senha-forte-123", role=CustomUser.Role.RESPONSAVEL
        )
        responsavel = Responsavel.objects.create(
            user=resp_user, nome_completo="Resp Dash", cpf="321.321.321-00", telefone="81900009999"
        )
        AlunoResponsavel.objects.create(
            aluno=meu_filho,
            responsavel=responsavel,
            parentesco=AlunoResponsavel.Parentesco.MAE,
            responsavel_financeiro=True,
        )
        Cobranca.objects.create(
            aluno=meu_filho,
            plano=plano,
            competencia="2020-01",
            valor_original=Decimal("500.00"),
            data_vencimento=date(2020, 1, 10),
            responsavel_financeiro=responsavel,
        )
        Cobranca.objects.create(
            aluno=filho_alheio,
            plano=plano,
            competencia="2020-01",
            valor_original=Decimal("999.00"),
            data_vencimento=date(2020, 1, 10),
        )

        client.login(username="resp.dash@escola.test", password="senha-forte-123")
        response = client.get(reverse("dashboard:responsavel"))

        assert response.status_code == 200
        assert response.context["total_cobrancas_atrasadas"] == 1
        assert response.context["valor_atrasado"] == Decimal("500.00")


@pytest.mark.django_db
class TestAlunoDashboard:
    def test_media_e_frequencia_calculadas_apenas_com_dados_do_proprio_aluno(self, client, turma, ano_letivo):
        disciplina = Disciplina.objects.create(nome="Ciências Sociais", codigo="CSO")
        prof_user = CustomUser.objects.create_user(
            email="prof.aluno.dash@escola.test", password="senha-forte-123", role=CustomUser.Role.PROFESSOR
        )
        professor = Professor.objects.create(user=prof_user)
        ProfessorDisciplinaTurma.objects.create(
            professor=professor, turma=turma, disciplina=disciplina, ano_letivo=ano_letivo
        )
        periodo = PeriodoLetivo.objects.create(
            ano_letivo=ano_letivo,
            numero=1,
            nome="1º Bimestre",
            data_inicio="2026-02-02",
            data_fim="2026-04-15",
        )
        tipo = TipoAvaliacao.objects.create(nome="Prova", peso=1)

        aluno_user = CustomUser.objects.create_user(
            email="aluno.dash@escola.test", password="senha-forte-123", role=CustomUser.Role.ALUNO
        )
        aluno = Aluno.objects.create(
            user=aluno_user,
            nome_completo="Aluno Dash",
            data_nascimento="2015-01-01",
            matricula_numero="D020",
            data_matricula_inicial="2026-02-02",
        )
        Matricula.objects.create(aluno=aluno, turma=turma, ano_letivo=ano_letivo, data_matricula="2026-02-02")

        avaliacao = Avaliacao.objects.create(
            turma=turma,
            disciplina=disciplina,
            professor=professor,
            periodo=periodo,
            tipo=tipo,
            titulo="Prova 1",
            data="2026-03-10",
        )
        Nota.objects.create(avaliacao=avaliacao, aluno=aluno, valor=Decimal("8.0"))

        aula = Aula.objects.create(turma=turma, disciplina=disciplina, professor=professor, data="2026-03-10")
        PresencaAluno.objects.create(aula=aula, aluno=aluno, status=PresencaAluno.Status.PRESENTE)

        client.login(username="aluno.dash@escola.test", password="senha-forte-123")
        response = client.get(reverse("dashboard:aluno"))

        assert response.status_code == 200
        assert response.context["media_geral"] == Decimal("8.0")
        assert response.context["frequencia_geral"] == 100.0

    def test_aluno_sem_cadastro_vinculado_nao_quebra(self, client):
        CustomUser.objects.create_user(
            email="sem.cadastro@escola.test", password="senha-forte-123", role=CustomUser.Role.ALUNO
        )
        client.login(username="sem.cadastro@escola.test", password="senha-forte-123")

        response = client.get(reverse("dashboard:aluno"))

        assert response.status_code == 200
        assert response.context["media_geral"] is None
