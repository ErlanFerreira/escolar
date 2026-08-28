import pytest
from django.urls import reverse

from apps.accounts.models import CustomUser
from apps.alunos.models import Aluno, AlunoResponsavel, Matricula, Responsavel
from apps.escola.models import AnoLetivo, Disciplina, Serie, Turma
from apps.frequencia.models import Aula, PresencaAluno
from apps.frequencia.relatorio import calcular_frequencia
from apps.professores.models import Professor, ProfessorDisciplinaTurma


@pytest.fixture
def ano_letivo(db):
    return AnoLetivo.objects.create(ano=2026, data_inicio="2026-02-02", data_fim="2026-12-18", ativo=True)


@pytest.fixture
def serie(db):
    return Serie.objects.create(nome="4º ano", segmento=Serie.Segmento.FUNDAMENTAL_I, ordem=4)


@pytest.fixture
def turma(db, ano_letivo, serie):
    return Turma.objects.create(ano_letivo=ano_letivo, serie=serie, nome="A", turno=Turma.Turno.MANHA)


@pytest.fixture
def disciplina(db):
    return Disciplina.objects.create(nome="História", codigo="HIS")


@pytest.fixture
def professor(db, turma, disciplina, ano_letivo):
    user = CustomUser.objects.create_user(
        email="prof.his@escola.test", password="senha-forte-123", role=CustomUser.Role.PROFESSOR
    )
    professor = Professor.objects.create(user=user)
    ProfessorDisciplinaTurma.objects.create(
        professor=professor, turma=turma, disciplina=disciplina, ano_letivo=ano_letivo
    )
    return professor


@pytest.fixture
def aluno_matriculado(db, turma, ano_letivo):
    aluno = Aluno.objects.create(
        nome_completo="Lucas Teste",
        data_nascimento="2016-06-01",
        matricula_numero="20260020",
        data_matricula_inicial="2026-02-02",
    )
    Matricula.objects.create(aluno=aluno, turma=turma, ano_letivo=ano_letivo, data_matricula="2026-02-02")
    return aluno


@pytest.mark.django_db
class TestChamadaView:
    def test_get_cria_aula_e_presencas_para_matriculados(
        self, client, professor, turma, disciplina, aluno_matriculado
    ):
        client.login(username=professor.user.email, password="senha-forte-123")
        url = reverse("frequencia:chamada", args=[turma.pk, disciplina.pk])

        response = client.get(url, {"data": "2026-03-05"})

        assert response.status_code == 200
        aula = Aula.objects.get(turma=turma, disciplina=disciplina, data="2026-03-05")
        assert aula.professor == professor
        presenca = PresencaAluno.objects.get(aula=aula, aluno=aluno_matriculado)
        assert presenca.status == PresencaAluno.Status.PRESENTE

    def test_post_salva_faltas_via_formset(self, client, professor, turma, disciplina, aluno_matriculado):
        client.login(username=professor.user.email, password="senha-forte-123")
        url = reverse("frequencia:chamada", args=[turma.pk, disciplina.pk])
        client.get(url, {"data": "2026-03-05"})
        presenca = PresencaAluno.objects.get(aluno=aluno_matriculado, aula__data="2026-03-05")

        response = client.post(
            url,
            {
                "data": "2026-03-05",
                "form-TOTAL_FORMS": "1",
                "form-INITIAL_FORMS": "1",
                "form-MIN_NUM_FORMS": "0",
                "form-MAX_NUM_FORMS": "1000",
                "form-0-id": str(presenca.pk),
                "form-0-status": "FALTA",
                "form-0-observacao": "",
            },
        )

        assert response.status_code == 302
        presenca.refresh_from_db()
        assert presenca.status == PresencaAluno.Status.FALTA

    def test_reabrir_chamada_do_mesmo_dia_nao_duplica_presenca(
        self, client, professor, turma, disciplina, aluno_matriculado
    ):
        client.login(username=professor.user.email, password="senha-forte-123")
        url = reverse("frequencia:chamada", args=[turma.pk, disciplina.pk])

        client.get(url, {"data": "2026-03-05"})
        client.get(url, {"data": "2026-03-05"})

        aula = Aula.objects.get(turma=turma, disciplina=disciplina, data="2026-03-05")
        assert PresencaAluno.objects.filter(aula=aula).count() == 1

    def test_outro_professor_nao_faz_chamada_de_turma_alheia(self, client, turma, disciplina):
        outro_user = CustomUser.objects.create_user(
            email="outro.prof.freq@escola.test", password="senha-forte-123", role=CustomUser.Role.PROFESSOR
        )
        Professor.objects.create(user=outro_user)
        client.login(username="outro.prof.freq@escola.test", password="senha-forte-123")

        response = client.get(reverse("frequencia:chamada", args=[turma.pk, disciplina.pk]))

        assert response.status_code == 404


@pytest.mark.django_db
class TestCalcularFrequencia:
    def test_percentual_considera_apenas_presente(self, professor, turma, disciplina, aluno_matriculado):
        datas = ["2026-03-02", "2026-03-03", "2026-03-04", "2026-03-05"]
        status = [
            PresencaAluno.Status.PRESENTE,
            PresencaAluno.Status.PRESENTE,
            PresencaAluno.Status.FALTA,
            PresencaAluno.Status.FALTA_JUSTIFICADA,
        ]
        for data, st in zip(datas, status, strict=True):
            aula = Aula.objects.create(turma=turma, disciplina=disciplina, professor=professor, data=data)
            PresencaAluno.objects.create(aula=aula, aluno=aluno_matriculado, status=st)

        relatorio = calcular_frequencia(aluno_matriculado)

        assert len(relatorio) == 1
        item = relatorio[0]
        assert item["total"] == 4
        assert item["presentes"] == 2
        assert item["percentual"] == 50.0

    def test_sem_chamadas_relatorio_vazio(self, aluno_matriculado):
        assert calcular_frequencia(aluno_matriculado) == []


@pytest.mark.django_db
class TestFrequenciaForUser:
    def test_responsavel_ve_frequencia_do_proprio_filho(
        self, client, professor, turma, disciplina, aluno_matriculado
    ):
        aula = Aula.objects.create(turma=turma, disciplina=disciplina, professor=professor, data="2026-03-05")
        PresencaAluno.objects.create(aula=aula, aluno=aluno_matriculado, status=PresencaAluno.Status.PRESENTE)

        resp_user = CustomUser.objects.create_user(
            email="pai.lucas@escola.test", password="senha-forte-123", role=CustomUser.Role.RESPONSAVEL
        )
        responsavel = Responsavel.objects.create(
            user=resp_user, nome_completo="Pai do Lucas", cpf="666.666.666-66", telefone="81900003333"
        )
        AlunoResponsavel.objects.create(
            aluno=aluno_matriculado, responsavel=responsavel, parentesco=AlunoResponsavel.Parentesco.PAI
        )

        client.login(username="pai.lucas@escola.test", password="senha-forte-123")
        response = client.get(reverse("frequencia:relatorio_filho", args=[aluno_matriculado.pk]))

        assert response.status_code == 200
        assert "100,0% de presen" in response.content.decode()

    def test_responsavel_nao_ve_frequencia_de_aluno_alheio(self, client, aluno_matriculado):
        resp_user = CustomUser.objects.create_user(
            email="estranho.freq@escola.test", password="senha-forte-123", role=CustomUser.Role.RESPONSAVEL
        )
        Responsavel.objects.create(
            user=resp_user, nome_completo="Estranho", cpf="777.777.777-77", telefone="81900004444"
        )

        client.login(username="estranho.freq@escola.test", password="senha-forte-123")
        response = client.get(reverse("frequencia:relatorio_filho", args=[aluno_matriculado.pk]))

        assert response.status_code == 404
