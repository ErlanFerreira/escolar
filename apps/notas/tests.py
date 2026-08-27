from decimal import Decimal

import pytest
from django.urls import reverse

from apps.accounts.models import CustomUser
from apps.alunos.models import Aluno, AlunoResponsavel, Matricula, Responsavel
from apps.escola.models import AnoLetivo, Serie, Turma
from apps.notas.boletim import montar_boletim
from apps.notas.models import Avaliacao, Nota, PeriodoLetivo, TipoAvaliacao
from apps.professores.models import Professor, ProfessorDisciplinaTurma


@pytest.fixture
def ano_letivo(db):
    return AnoLetivo.objects.create(ano=2026, data_inicio="2026-02-02", data_fim="2026-12-18", ativo=True)


@pytest.fixture
def serie(db):
    return Serie.objects.create(nome="5º ano", segmento=Serie.Segmento.FUNDAMENTAL_I, ordem=5)


@pytest.fixture
def turma(db, ano_letivo, serie):
    return Turma.objects.create(ano_letivo=ano_letivo, serie=serie, nome="A", turno=Turma.Turno.MANHA)


@pytest.fixture
def disciplina(db):
    from apps.escola.models import Disciplina

    return Disciplina.objects.create(nome="Ciências", codigo="CIE")


@pytest.fixture
def periodo(db, ano_letivo):
    return PeriodoLetivo.objects.create(
        ano_letivo=ano_letivo, numero=1, nome="1º Bimestre", data_inicio="2026-02-02", data_fim="2026-04-15"
    )


@pytest.fixture
def tipo_avaliacao(db):
    return TipoAvaliacao.objects.create(nome="Prova", peso=Decimal("1"))


@pytest.fixture
def professor(db, turma, disciplina, ano_letivo):
    user = CustomUser.objects.create_user(
        email="prof.cie@escola.test", password="senha-forte-123", role=CustomUser.Role.PROFESSOR
    )
    professor = Professor.objects.create(user=user)
    ProfessorDisciplinaTurma.objects.create(
        professor=professor, turma=turma, disciplina=disciplina, ano_letivo=ano_letivo
    )
    return professor


@pytest.fixture
def aluno_matriculado(db, turma, ano_letivo):
    aluno = Aluno.objects.create(
        nome_completo="Pedro Teste",
        data_nascimento="2016-01-01",
        matricula_numero="20260010",
        data_matricula_inicial="2026-02-02",
    )
    Matricula.objects.create(aluno=aluno, turma=turma, ano_letivo=ano_letivo, data_matricula="2026-02-02")
    return aluno


@pytest.mark.django_db
class TestAvaliacaoCreateView:
    def test_professor_cria_avaliacao_e_notas_sao_geradas_para_matriculados(
        self, client, professor, turma, disciplina, periodo, tipo_avaliacao, aluno_matriculado
    ):
        client.login(username=professor.user.email, password="senha-forte-123")
        url = reverse("notas:nova_avaliacao", args=[turma.pk, disciplina.pk])

        response = client.post(
            url,
            {
                "periodo": periodo.pk,
                "tipo": tipo_avaliacao.pk,
                "titulo": "Prova 1",
                "data": "2026-03-10",
                "valor_maximo": "10.00",
                "peso": "1.00",
            },
        )

        assert response.status_code == 302
        avaliacao = Avaliacao.objects.get(titulo="Prova 1")
        assert avaliacao.professor == professor
        assert Nota.objects.filter(avaliacao=avaliacao, aluno=aluno_matriculado, valor__isnull=True).exists()

    def test_professor_de_outra_disciplina_nao_pode_criar_avaliacao(
        self, client, turma, disciplina, ano_letivo
    ):
        outro_user = CustomUser.objects.create_user(
            email="outro.prof@escola.test", password="senha-forte-123", role=CustomUser.Role.PROFESSOR
        )
        Professor.objects.create(user=outro_user)
        client.login(username="outro.prof@escola.test", password="senha-forte-123")
        url = reverse("notas:nova_avaliacao", args=[turma.pk, disciplina.pk])

        response = client.get(url)

        assert response.status_code == 404


@pytest.mark.django_db
class TestLancarNotas:
    def test_professor_lanca_notas_via_formset(
        self, client, professor, turma, disciplina, periodo, tipo_avaliacao, aluno_matriculado
    ):
        avaliacao = Avaliacao.objects.create(
            turma=turma,
            disciplina=disciplina,
            professor=professor,
            periodo=periodo,
            tipo=tipo_avaliacao,
            titulo="Prova 1",
            data="2026-03-10",
        )
        nota = Nota.objects.create(avaliacao=avaliacao, aluno=aluno_matriculado)

        client.login(username=professor.user.email, password="senha-forte-123")
        url = reverse("notas:lancar", args=[avaliacao.pk])
        response = client.post(
            url,
            {
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "1",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-id": str(nota.pk),
                "form-0-valor": "8.5",
                "form-0-observacao": "",
            },
        )

        assert response.status_code == 302
        nota.refresh_from_db()
        assert nota.valor == Decimal("8.5")

    def test_outro_professor_nao_acessa_avaliacao_alheia(
        self, client, professor, turma, disciplina, periodo, tipo_avaliacao, aluno_matriculado
    ):
        avaliacao = Avaliacao.objects.create(
            turma=turma,
            disciplina=disciplina,
            professor=professor,
            periodo=periodo,
            tipo=tipo_avaliacao,
            titulo="Prova 1",
            data="2026-03-10",
        )
        outro_user = CustomUser.objects.create_user(
            email="outro2@escola.test", password="senha-forte-123", role=CustomUser.Role.PROFESSOR
        )
        Professor.objects.create(user=outro_user)
        client.login(username="outro2@escola.test", password="senha-forte-123")

        response = client.get(reverse("notas:lancar", args=[avaliacao.pk]))

        assert response.status_code == 404


@pytest.mark.django_db
class TestBoletim:
    def test_media_ponderada_pelo_peso_da_avaliacao(
        self, turma, disciplina, professor, periodo, aluno_matriculado
    ):
        tipo_prova = TipoAvaliacao.objects.create(nome="Prova", peso=Decimal("1"))
        avaliacao_1 = Avaliacao.objects.create(
            turma=turma,
            disciplina=disciplina,
            professor=professor,
            periodo=periodo,
            tipo=tipo_prova,
            titulo="Prova 1",
            data="2026-03-10",
            peso=Decimal("2"),
        )
        avaliacao_2 = Avaliacao.objects.create(
            turma=turma,
            disciplina=disciplina,
            professor=professor,
            periodo=periodo,
            tipo=tipo_prova,
            titulo="Prova 2",
            data="2026-04-10",
            peso=Decimal("1"),
        )
        Nota.objects.create(avaliacao=avaliacao_1, aluno=aluno_matriculado, valor=Decimal("8.0"))
        Nota.objects.create(avaliacao=avaliacao_2, aluno=aluno_matriculado, valor=Decimal("5.0"))

        boletim = montar_boletim(aluno_matriculado)

        assert len(boletim) == 1
        # (8*2 + 5*1) / (2+1) = 21/3 = 7
        assert boletim[0]["media"] == Decimal("7.00")

    def test_notas_nao_lancadas_nao_entram_no_boletim(
        self, turma, disciplina, professor, periodo, aluno_matriculado, tipo_avaliacao
    ):
        avaliacao = Avaliacao.objects.create(
            turma=turma,
            disciplina=disciplina,
            professor=professor,
            periodo=periodo,
            tipo=tipo_avaliacao,
            titulo="Prova 1",
            data="2026-03-10",
        )
        Nota.objects.create(avaliacao=avaliacao, aluno=aluno_matriculado, valor=None)

        assert montar_boletim(aluno_matriculado) == []


@pytest.mark.django_db
class TestBoletimForUser:
    def test_responsavel_ve_boletim_do_proprio_filho(
        self, client, turma, disciplina, professor, periodo, tipo_avaliacao, aluno_matriculado
    ):
        avaliacao = Avaliacao.objects.create(
            turma=turma,
            disciplina=disciplina,
            professor=professor,
            periodo=periodo,
            tipo=tipo_avaliacao,
            titulo="Prova 1",
            data="2026-03-10",
        )
        Nota.objects.create(avaliacao=avaliacao, aluno=aluno_matriculado, valor=Decimal("9.0"))

        resp_user = CustomUser.objects.create_user(
            email="mae.pedro@escola.test", password="senha-forte-123", role=CustomUser.Role.RESPONSAVEL
        )
        responsavel = Responsavel.objects.create(
            user=resp_user, nome_completo="Mãe do Pedro", cpf="444.444.444-44", telefone="81900001111"
        )
        AlunoResponsavel.objects.create(
            aluno=aluno_matriculado, responsavel=responsavel, parentesco=AlunoResponsavel.Parentesco.MAE
        )

        client.login(username="mae.pedro@escola.test", password="senha-forte-123")
        response = client.get(reverse("notas:boletim_filho", args=[aluno_matriculado.pk]))

        assert response.status_code == 200
        # LANGUAGE_CODE=pt-br localiza números com vírgula decimal (9,00), não ponto.
        assert "9,00" in response.content.decode()

    def test_responsavel_nao_ve_boletim_de_aluno_alheio(self, client, aluno_matriculado):
        resp_user = CustomUser.objects.create_user(
            email="estranho@escola.test", password="senha-forte-123", role=CustomUser.Role.RESPONSAVEL
        )
        Responsavel.objects.create(
            user=resp_user, nome_completo="Estranho", cpf="555.555.555-55", telefone="81900002222"
        )

        client.login(username="estranho@escola.test", password="senha-forte-123")
        response = client.get(reverse("notas:boletim_filho", args=[aluno_matriculado.pk]))

        assert response.status_code == 404
