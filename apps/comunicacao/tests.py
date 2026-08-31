import pytest
from django.urls import reverse

from apps.accounts.models import CustomUser
from apps.alunos.models import Aluno, AlunoResponsavel, Matricula, Responsavel
from apps.comunicacao.destinatarios import calcular_destinatarios
from apps.comunicacao.models import Comunicado, ComunicadoLeitura
from apps.escola.models import AnoLetivo, Serie, Turma
from apps.professores.models import Professor, ProfessorDisciplinaTurma


@pytest.fixture
def ano_letivo(db):
    return AnoLetivo.objects.create(ano=2026, data_inicio="2026-02-02", data_fim="2026-12-18", ativo=True)


@pytest.fixture
def serie(db):
    return Serie.objects.create(nome="2º ano", segmento=Serie.Segmento.FUNDAMENTAL_I, ordem=2)


@pytest.fixture
def turma_a(db, ano_letivo, serie):
    return Turma.objects.create(ano_letivo=ano_letivo, serie=serie, nome="A", turno=Turma.Turno.MANHA)


@pytest.fixture
def turma_b(db, ano_letivo, serie):
    return Turma.objects.create(ano_letivo=ano_letivo, serie=serie, nome="B", turno=Turma.Turno.TARDE)


@pytest.fixture
def secretaria(db):
    return CustomUser.objects.create_user(
        email="sec.com@escola.test", password="senha-forte-123", role=CustomUser.Role.SECRETARIA
    )


@pytest.fixture
def professor_turma_a(db, turma_a):
    from apps.escola.models import Disciplina

    user = CustomUser.objects.create_user(
        email="prof.a@escola.test", password="senha-forte-123", role=CustomUser.Role.PROFESSOR
    )
    professor = Professor.objects.create(user=user)
    disciplina = Disciplina.objects.create(nome="Artes", codigo="ART")
    ProfessorDisciplinaTurma.objects.create(
        professor=professor, turma=turma_a, disciplina=disciplina, ano_letivo=turma_a.ano_letivo
    )
    return professor


@pytest.fixture
def familia_turma_a(db, turma_a):
    """Aluno matriculado na turma A, com responsável e conta de aluno vinculadas."""
    aluno_user = CustomUser.objects.create_user(
        email="aluno.a@escola.test", password="senha-forte-123", role=CustomUser.Role.ALUNO
    )
    aluno = Aluno.objects.create(
        user=aluno_user,
        nome_completo="Aluno Turma A",
        data_nascimento="2018-01-01",
        matricula_numero="20260040",
        data_matricula_inicial="2026-02-02",
    )
    Matricula.objects.create(
        aluno=aluno, turma=turma_a, ano_letivo=turma_a.ano_letivo, data_matricula="2026-02-02"
    )

    resp_user = CustomUser.objects.create_user(
        email="resp.a@escola.test", password="senha-forte-123", role=CustomUser.Role.RESPONSAVEL
    )
    responsavel = Responsavel.objects.create(
        user=resp_user, nome_completo="Responsável A", cpf="888.888.888-88", telefone="81900005555"
    )
    AlunoResponsavel.objects.create(
        aluno=aluno,
        responsavel=responsavel,
        parentesco=AlunoResponsavel.Parentesco.MAE,
        responsavel_pedagogico=True,
    )
    return {"aluno": aluno, "aluno_user": aluno_user, "responsavel": responsavel, "resp_user": resp_user}


@pytest.mark.django_db
class TestSegmentacaoTodos:
    def test_todos_aparece_para_qualquer_perfil(self, secretaria, professor_turma_a, familia_turma_a):
        comunicado = Comunicado.objects.create(
            titulo="Recesso escolar",
            corpo="Aviso geral",
            autor=secretaria,
            publico_alvo=Comunicado.PublicoAlvo.TODOS,
        )

        assert comunicado in Comunicado.objects.for_user(professor_turma_a.user)
        assert comunicado in Comunicado.objects.for_user(familia_turma_a["resp_user"])
        assert comunicado in Comunicado.objects.for_user(familia_turma_a["aluno_user"])


@pytest.mark.django_db
class TestSegmentacaoProfessores:
    def test_apenas_professores_veem(self, secretaria, professor_turma_a, familia_turma_a):
        comunicado = Comunicado.objects.create(
            titulo="Reunião pedagógica",
            corpo="Aviso para professores",
            autor=secretaria,
            publico_alvo=Comunicado.PublicoAlvo.PROFESSORES,
        )

        assert comunicado in Comunicado.objects.for_user(professor_turma_a.user)
        assert comunicado not in Comunicado.objects.for_user(familia_turma_a["resp_user"])
        assert comunicado not in Comunicado.objects.for_user(familia_turma_a["aluno_user"])


@pytest.mark.django_db
class TestSegmentacaoTurmaEspecifica:
    def test_turma_especifica_so_aparece_para_quem_pertence_a_ela(
        self, secretaria, professor_turma_a, familia_turma_a, turma_a, turma_b
    ):
        comunicado = Comunicado.objects.create(
            titulo="Passeio da turma A",
            corpo="Detalhes do passeio",
            autor=secretaria,
            publico_alvo=Comunicado.PublicoAlvo.TURMA_ESPECIFICA,
        )
        comunicado.turmas.add(turma_a)

        # Pertencem à turma A: veem
        assert comunicado in Comunicado.objects.for_user(professor_turma_a.user)
        assert comunicado in Comunicado.objects.for_user(familia_turma_a["resp_user"])
        assert comunicado in Comunicado.objects.for_user(familia_turma_a["aluno_user"])

        # Professor de outra turma não vê
        from apps.escola.models import Disciplina

        outro_user = CustomUser.objects.create_user(
            email="prof.b@escola.test", password="senha-forte-123", role=CustomUser.Role.PROFESSOR
        )
        outro_professor = Professor.objects.create(user=outro_user)
        disciplina_b = Disciplina.objects.create(nome="Educação Física", codigo="EDF")
        ProfessorDisciplinaTurma.objects.create(
            professor=outro_professor, turma=turma_b, disciplina=disciplina_b, ano_letivo=turma_b.ano_letivo
        )

        assert comunicado not in Comunicado.objects.for_user(outro_user)

    def test_calcular_destinatarios_inclui_professor_responsavel_e_aluno_da_turma(
        self, secretaria, professor_turma_a, familia_turma_a, turma_a
    ):
        comunicado = Comunicado.objects.create(
            titulo="Passeio da turma A",
            corpo="Detalhes do passeio",
            autor=secretaria,
            publico_alvo=Comunicado.PublicoAlvo.TURMA_ESPECIFICA,
        )
        comunicado.turmas.add(turma_a)

        destinatarios = calcular_destinatarios(comunicado)

        assert professor_turma_a.user in destinatarios
        assert familia_turma_a["resp_user"] in destinatarios
        assert familia_turma_a["aluno_user"] in destinatarios
        assert secretaria not in destinatarios


@pytest.mark.django_db
class TestConfirmacaoDeLeitura:
    def test_abrir_comunicado_marca_como_lido(self, client, secretaria, familia_turma_a):
        comunicado = Comunicado.objects.create(
            titulo="Aviso", corpo="Corpo", autor=secretaria, publico_alvo=Comunicado.PublicoAlvo.TODOS
        )
        client.login(username=familia_turma_a["resp_user"].email, password="senha-forte-123")

        assert not ComunicadoLeitura.objects.filter(
            comunicado=comunicado, user=familia_turma_a["resp_user"], lida_em__isnull=False
        ).exists()

        response = client.get(reverse("comunicacao:detalhe", args=[comunicado.pk]))

        assert response.status_code == 200
        assert ComunicadoLeitura.objects.filter(
            comunicado=comunicado, user=familia_turma_a["resp_user"], lida_em__isnull=False
        ).exists()

    def test_relatorio_de_leitura_conta_apenas_destinatarios_reais(
        self, client, secretaria, professor_turma_a, familia_turma_a
    ):
        comunicado = Comunicado.objects.create(
            titulo="Reunião pedagógica",
            corpo="Aviso para professores",
            autor=secretaria,
            publico_alvo=Comunicado.PublicoAlvo.PROFESSORES,
        )
        client.login(username=professor_turma_a.user.email, password="senha-forte-123")
        client.get(reverse("comunicacao:detalhe", args=[comunicado.pk]))

        client.logout()
        client.login(username=secretaria.email, password="senha-forte-123")
        response = client.get(reverse("comunicacao:detalhe", args=[comunicado.pk]))

        assert response.status_code == 200
        assert "1 de 1 destinat" in response.content.decode()


@pytest.mark.django_db
class TestCriarComunicado:
    def test_secretaria_cria_comunicado(self, client, secretaria, turma_a):
        client.login(username=secretaria.email, password="senha-forte-123")

        response = client.post(
            reverse("comunicacao:criar"),
            {
                "titulo": "Feriado",
                "corpo": "Não haverá aula na sexta-feira.",
                "publico_alvo": Comunicado.PublicoAlvo.TODOS,
                "turmas": [],
                "urgente": "on",
            },
        )

        assert response.status_code == 302
        comunicado = Comunicado.objects.get(titulo="Feriado")
        assert comunicado.autor == secretaria
        assert comunicado.urgente is True

    def test_professor_nao_pode_criar_comunicado(self, client, professor_turma_a):
        client.login(username=professor_turma_a.user.email, password="senha-forte-123")

        response = client.get(reverse("comunicacao:criar"))

        assert response.status_code == 403
