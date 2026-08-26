import pytest

from apps.accounts.models import CustomUser
from apps.escola.models import AnoLetivo, Disciplina, Serie, Turma
from apps.professores.models import Professor, ProfessorDisciplinaTurma


@pytest.fixture
def ano_letivo(db):
    return AnoLetivo.objects.create(ano=2026, data_inicio="2026-02-02", data_fim="2026-12-18")


@pytest.fixture
def serie(db):
    return Serie.objects.create(nome="6º ano", segmento=Serie.Segmento.FUNDAMENTAL_II, ordem=6)


@pytest.fixture
def disciplina(db):
    return Disciplina.objects.create(nome="Matemática", codigo="MAT")


@pytest.fixture
def outra_disciplina(db):
    return Disciplina.objects.create(nome="Português", codigo="POR")


@pytest.mark.django_db
class TestTurmaForUser:
    def _criar_professor(self, email):
        user = CustomUser.objects.create_user(
            email=email, password="senha-forte-123", role=CustomUser.Role.PROFESSOR
        )
        return Professor.objects.create(user=user)

    def test_secretaria_ve_todas_as_turmas(self, ano_letivo, serie):
        secretaria = CustomUser.objects.create_user(
            email="secretaria@escola.test", password="senha-forte-123", role=CustomUser.Role.SECRETARIA
        )
        turma_a = Turma.objects.create(ano_letivo=ano_letivo, serie=serie, nome="A", turno=Turma.Turno.MANHA)
        turma_b = Turma.objects.create(ano_letivo=ano_letivo, serie=serie, nome="B", turno=Turma.Turno.TARDE)

        turmas = Turma.objects.for_user(secretaria)

        assert set(turmas) == {turma_a, turma_b}

    def test_professor_ve_apenas_suas_turmas_atribuidas(
        self, ano_letivo, serie, disciplina, outra_disciplina
    ):
        professor = self._criar_professor("professor.mat@escola.test")
        outro_professor = self._criar_professor("professor.por@escola.test")

        turma_do_professor = Turma.objects.create(
            ano_letivo=ano_letivo, serie=serie, nome="A", turno=Turma.Turno.MANHA
        )
        turma_de_outro_professor = Turma.objects.create(
            ano_letivo=ano_letivo, serie=serie, nome="B", turno=Turma.Turno.TARDE
        )

        ProfessorDisciplinaTurma.objects.create(
            professor=professor, turma=turma_do_professor, disciplina=disciplina, ano_letivo=ano_letivo
        )
        ProfessorDisciplinaTurma.objects.create(
            professor=outro_professor,
            turma=turma_de_outro_professor,
            disciplina=outra_disciplina,
            ano_letivo=ano_letivo,
        )

        turmas = Turma.objects.for_user(professor.user)

        assert set(turmas) == {turma_do_professor}

    def test_professor_sem_atribuicoes_nao_ve_turmas(self, ano_letivo, serie):
        professor = self._criar_professor("sem.turma@escola.test")
        Turma.objects.create(ano_letivo=ano_letivo, serie=serie, nome="A", turno=Turma.Turno.MANHA)

        assert list(Turma.objects.for_user(professor.user)) == []

    def test_responsavel_nao_ve_nenhuma_turma_ainda(self, ano_letivo, serie):
        responsavel = CustomUser.objects.create_user(
            email="resp@escola.test", password="senha-forte-123", role=CustomUser.Role.RESPONSAVEL
        )
        Turma.objects.create(ano_letivo=ano_letivo, serie=serie, nome="A", turno=Turma.Turno.MANHA)

        assert list(Turma.objects.for_user(responsavel)) == []
