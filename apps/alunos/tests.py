import pytest
from django.urls import reverse

from apps.accounts.models import CustomUser
from apps.alunos.models import Aluno, AlunoResponsavel, Matricula, Responsavel
from apps.escola.models import AnoLetivo, Serie, Turma


@pytest.fixture
def ano_letivo(db):
    return AnoLetivo.objects.create(ano=2026, data_inicio="2026-02-02", data_fim="2026-12-18", ativo=True)


@pytest.fixture
def serie(db):
    return Serie.objects.create(nome="1º ano", segmento=Serie.Segmento.FUNDAMENTAL_I, ordem=1)


@pytest.fixture
def turma(db, ano_letivo, serie):
    return Turma.objects.create(ano_letivo=ano_letivo, serie=serie, nome="A", turno=Turma.Turno.MANHA)


@pytest.fixture
def aluno(db):
    return Aluno.objects.create(
        nome_completo="Maria Teste",
        data_nascimento="2016-05-10",
        matricula_numero="20260001",
        data_matricula_inicial="2026-02-02",
    )


@pytest.fixture
def responsavel(db):
    return Responsavel.objects.create(nome_completo="Ana Teste", cpf="111.111.111-11", telefone="81999990000")


@pytest.mark.django_db
class TestModelConstraints:
    def test_matricula_unica_por_aluno_e_ano_letivo(self, aluno, turma, ano_letivo):
        Matricula.objects.create(aluno=aluno, turma=turma, ano_letivo=ano_letivo, data_matricula="2026-02-02")

        with pytest.raises(Exception):
            Matricula.objects.create(
                aluno=aluno, turma=turma, ano_letivo=ano_letivo, data_matricula="2026-02-03"
            )

    def test_vinculo_aluno_responsavel_unico(self, aluno, responsavel):
        AlunoResponsavel.objects.create(
            aluno=aluno, responsavel=responsavel, parentesco=AlunoResponsavel.Parentesco.MAE
        )

        with pytest.raises(Exception):
            AlunoResponsavel.objects.create(
                aluno=aluno, responsavel=responsavel, parentesco=AlunoResponsavel.Parentesco.MAE
            )


@pytest.mark.django_db
class TestForUserScoping:
    def test_responsavel_ve_apenas_os_proprios_filhos(self, aluno, responsavel):
        outro_aluno = Aluno.objects.create(
            nome_completo="Outro Aluno",
            data_nascimento="2015-01-01",
            matricula_numero="20260002",
            data_matricula_inicial="2026-02-02",
        )
        resp_user = CustomUser.objects.create_user(
            email="mae@escola.test", password="senha-forte-123", role=CustomUser.Role.RESPONSAVEL
        )
        responsavel.user = resp_user
        responsavel.save()
        AlunoResponsavel.objects.create(
            aluno=aluno, responsavel=responsavel, parentesco=AlunoResponsavel.Parentesco.MAE
        )

        alunos_visiveis = Aluno.objects.for_user(resp_user)

        assert set(alunos_visiveis) == {aluno}
        assert outro_aluno not in alunos_visiveis

    def test_aluno_ve_apenas_os_proprios_dados(self, aluno):
        aluno_user = CustomUser.objects.create_user(
            email="maria@escola.test", password="senha-forte-123", role=CustomUser.Role.ALUNO
        )
        aluno.user = aluno_user
        aluno.save()
        Aluno.objects.create(
            nome_completo="Outro Aluno",
            data_nascimento="2015-01-01",
            matricula_numero="20260003",
            data_matricula_inicial="2026-02-02",
        )

        assert set(Aluno.objects.for_user(aluno_user)) == {aluno}

    def test_turma_for_user_inclui_turma_do_filho_do_responsavel(self, aluno, responsavel, turma, ano_letivo):
        resp_user = CustomUser.objects.create_user(
            email="pai@escola.test", password="senha-forte-123", role=CustomUser.Role.RESPONSAVEL
        )
        responsavel.user = resp_user
        responsavel.save()
        AlunoResponsavel.objects.create(
            aluno=aluno, responsavel=responsavel, parentesco=AlunoResponsavel.Parentesco.PAI
        )
        Matricula.objects.create(aluno=aluno, turma=turma, ano_letivo=ano_letivo, data_matricula="2026-02-02")

        assert set(Turma.objects.for_user(resp_user)) == {turma}


@pytest.mark.django_db
class TestMatriculaWizard:
    def test_fluxo_completo_cria_aluno_responsavel_e_matricula(self, client, turma):
        CustomUser.objects.create_user(
            email="secretaria@escola.test", password="senha-forte-123", role=CustomUser.Role.SECRETARIA
        )
        client.login(username="secretaria@escola.test", password="senha-forte-123")
        url = reverse("alunos:matricular")

        step1 = client.post(
            url,
            {
                "matricula_wizard_view-current_step": "aluno",
                "aluno-nome_completo": "João da Silva",
                "aluno-data_nascimento": "2017-03-15",
                "aluno-cpf": "",
                "aluno-rg": "",
                "aluno-sexo": "M",
                "aluno-observacoes": "",
            },
        )
        assert step1.status_code == 200

        step2 = client.post(
            url,
            {
                "matricula_wizard_view-current_step": "responsaveis",
                "responsaveis-TOTAL_FORMS": "2",
                "responsaveis-INITIAL_FORMS": "0",
                "responsaveis-MIN_NUM_FORMS": "0",
                "responsaveis-MAX_NUM_FORMS": "1000",
                "responsaveis-0-nome_completo": "Maria da Silva",
                "responsaveis-0-cpf": "222.222.222-22",
                "responsaveis-0-telefone": "81988887777",
                "responsaveis-0-telefone_secundario": "",
                "responsaveis-0-email": "",
                "responsaveis-0-endereco": "",
                "responsaveis-0-profissao": "",
                "responsaveis-0-parentesco": "MAE",
                "responsaveis-0-responsavel_financeiro": "on",
                "responsaveis-0-responsavel_pedagogico": "on",
                "responsaveis-0-reside_com_aluno": "on",
                "responsaveis-1-nome_completo": "",
                "responsaveis-1-cpf": "",
                "responsaveis-1-telefone": "",
                "responsaveis-1-telefone_secundario": "",
                "responsaveis-1-email": "",
                "responsaveis-1-endereco": "",
                "responsaveis-1-profissao": "",
                "responsaveis-1-parentesco": "",
            },
        )
        assert step2.status_code == 200

        step3 = client.post(
            url,
            {
                "matricula_wizard_view-current_step": "turma",
                "turma-turma": str(turma.pk),
            },
        )
        assert step3.status_code == 302

        aluno = Aluno.objects.get(nome_completo="João da Silva")
        assert aluno.matricula_numero
        assert Matricula.objects.filter(aluno=aluno, turma=turma).exists()
        vinculo = AlunoResponsavel.objects.get(aluno=aluno)
        assert vinculo.responsavel.nome_completo == "Maria da Silva"
        assert vinculo.parentesco == AlunoResponsavel.Parentesco.MAE
