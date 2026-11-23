import pytest
from django.urls import reverse

from apps.accounts.models import CustomUser
from apps.alunos.models import Aluno, AlunoResponsavel, Matricula, Responsavel
from apps.escola.models import AnoLetivo, Serie, Turma

MAE = {
    "nome_completo": "Mãe Com Acesso",
    "cpf": "101.101.101-01",
    "telefone": "81911110000",
    "email": "mae.acesso@exemplo.com",
    "parentesco": "MAE",
}


@pytest.fixture
def ano_letivo(db):
    return AnoLetivo.objects.create(ano=2026, data_inicio="2026-02-02", data_fim="2026-12-18", ativo=True)


@pytest.fixture
def turma(db, ano_letivo):
    serie = Serie.objects.create(nome="6º ano", segmento=Serie.Segmento.FUNDAMENTAL_II, ordem=6)
    return Turma.objects.create(ano_letivo=ano_letivo, serie=serie, nome="A", turno=Turma.Turno.MANHA)


@pytest.fixture
def secretaria_logada(client):
    CustomUser.objects.create_user(
        email="sec.acesso@escola.test", password="senha-forte-123", role=CustomUser.Role.SECRETARIA
    )
    client.login(username="sec.acesso@escola.test", password="senha-forte-123")
    return client


def rodar_wizard(client, turma, *, email_aluno="", responsaveis=None):
    """Percorre os 3 passos do wizard. ``responsaveis`` é uma lista de dicts (até 2)."""
    url = reverse("alunos:matricular")
    passo = "matricula_wizard_view-current_step"

    client.post(
        url,
        {
            passo: "aluno",
            "aluno-nome_completo": "Aluno Com Acesso",
            "aluno-data_nascimento": "2012-04-10",
            "aluno-cpf": "",
            "aluno-rg": "",
            "aluno-sexo": "M",
            "aluno-observacoes": "",
            "aluno-email_acesso": email_aluno,
        },
    )

    dados = {
        passo: "responsaveis",
        "responsaveis-TOTAL_FORMS": "2",
        "responsaveis-INITIAL_FORMS": "0",
        "responsaveis-MIN_NUM_FORMS": "0",
        "responsaveis-MAX_NUM_FORMS": "1000",
    }
    responsaveis = responsaveis or []
    for indice in range(2):
        r = responsaveis[indice] if indice < len(responsaveis) else {}
        p = f"responsaveis-{indice}-"
        dados.update(
            {
                p + "nome_completo": r.get("nome_completo", ""),
                p + "cpf": r.get("cpf", ""),
                p + "telefone": r.get("telefone", ""),
                p + "email": r.get("email", ""),
                p + "parentesco": r.get("parentesco", ""),
                p + "telefone_secundario": "",
                p + "endereco": "",
                p + "profissao": "",
            }
        )
    resposta = client.post(url, dados)
    if resposta.context is None or resposta.context["wizard"]["steps"].current != "turma":
        return resposta
    return client.post(url, {passo: "turma", "turma-turma": str(turma.pk)})


@pytest.mark.django_db
class TestAcessoNoWizard:
    def test_responsavel_com_email_ganha_login_com_senha_temporaria(self, secretaria_logada, turma):
        resposta = rodar_wizard(secretaria_logada, turma, responsaveis=[MAE])

        assert resposta.status_code == 200
        credencial = resposta.context["credenciais"][0]
        assert credencial["email"] == "mae.acesso@exemplo.com"
        usuario = CustomUser.objects.get(email="mae.acesso@exemplo.com")
        assert usuario.role == CustomUser.Role.RESPONSAVEL
        assert usuario.must_change_password is True
        assert usuario.check_password(credencial["senha"])
        assert Responsavel.objects.get(cpf=MAE["cpf"]).user == usuario
        assert credencial["senha"] in resposta.content.decode()
        assert "no-store" in resposta["Cache-Control"]

    def test_aluno_com_email_de_acesso_ganha_login(self, secretaria_logada, turma):
        resposta = rodar_wizard(
            secretaria_logada, turma, email_aluno="aluno.acesso@exemplo.com", responsaveis=[MAE]
        )

        usuario = CustomUser.objects.get(email="aluno.acesso@exemplo.com")
        assert usuario.role == CustomUser.Role.ALUNO
        assert usuario.must_change_password is True
        assert Aluno.objects.get(nome_completo="Aluno Com Acesso").user == usuario
        assert {c["perfil"] for c in resposta.context["credenciais"]} == {"Aluno", "Responsável"}

    def test_sem_emails_nao_cria_nenhum_login(self, secretaria_logada, turma):
        usuarios_antes = CustomUser.objects.count()

        resposta = rodar_wizard(secretaria_logada, turma, responsaveis=[{**MAE, "email": ""}])

        assert resposta.status_code == 200
        assert resposta.context["credenciais"] == []
        assert CustomUser.objects.count() == usuarios_antes
        assert Responsavel.objects.get(cpf=MAE["cpf"]).user is None

    def test_email_ja_usado_por_outra_conta_barra_o_passo_dos_responsaveis(self, secretaria_logada, turma):
        CustomUser.objects.create_user(
            email="mae.acesso@exemplo.com", password="x-senha-forte-1", role=CustomUser.Role.PROFESSOR
        )

        resposta = rodar_wizard(secretaria_logada, turma, responsaveis=[MAE])

        assert resposta.status_code == 200
        assert resposta.context["wizard"]["steps"].current == "responsaveis"
        assert not Aluno.objects.filter(nome_completo="Aluno Com Acesso").exists()

    def test_segundo_filho_reaproveita_o_login_do_mesmo_responsavel(self, secretaria_logada, turma):
        rodar_wizard(secretaria_logada, turma, responsaveis=[MAE])
        usuarios_antes = CustomUser.objects.count()

        resposta = rodar_wizard(secretaria_logada, turma, responsaveis=[MAE])

        assert resposta.status_code == 200
        assert CustomUser.objects.count() == usuarios_antes
        assert resposta.context["credenciais"] == []


@pytest.mark.django_db
class TestCriarAcessoDepois:
    def _aluno_sem_acesso(self, turma, ano_letivo):
        aluno = Aluno.objects.create(
            nome_completo="Sem Login",
            data_nascimento="2012-01-01",
            matricula_numero="20269001",
            data_matricula_inicial="2026-02-02",
        )
        Matricula.objects.create(aluno=aluno, turma=turma, ano_letivo=ano_letivo, data_matricula="2026-02-02")
        responsavel = Responsavel.objects.create(
            nome_completo="Resp Sem Login", cpf="202.202.202-02", telefone="81922220000"
        )
        AlunoResponsavel.objects.create(
            aluno=aluno, responsavel=responsavel, parentesco=AlunoResponsavel.Parentesco.PAI
        )
        return aluno, responsavel

    def test_secretaria_cria_acesso_do_responsavel_existente(self, secretaria_logada, turma, ano_letivo):
        aluno, responsavel = self._aluno_sem_acesso(turma, ano_letivo)

        resposta = secretaria_logada.post(
            reverse("alunos:acesso_responsavel", args=[aluno.pk, responsavel.pk]),
            {"email": "pai.depois@exemplo.com"},
        )

        assert resposta.status_code == 200
        responsavel.refresh_from_db()
        assert responsavel.user.email == "pai.depois@exemplo.com"
        assert responsavel.user.check_password(resposta.context["credenciais"][0]["senha"])

    def test_secretaria_cria_acesso_do_aluno_existente(self, secretaria_logada, turma, ano_letivo):
        aluno, _ = self._aluno_sem_acesso(turma, ano_letivo)

        resposta = secretaria_logada.post(
            reverse("alunos:acesso_aluno", args=[aluno.pk]), {"email": "aluno.depois@exemplo.com"}
        )

        assert resposta.status_code == 200
        aluno.refresh_from_db()
        assert aluno.user.role == CustomUser.Role.ALUNO

    def test_email_invalido_nao_cria_nada(self, secretaria_logada, turma, ano_letivo):
        aluno, _ = self._aluno_sem_acesso(turma, ano_letivo)

        resposta = secretaria_logada.post(
            reverse("alunos:acesso_aluno", args=[aluno.pk]), {"email": "isso-nao-e-email"}
        )

        assert resposta.status_code == 302
        aluno.refresh_from_db()
        assert aluno.user is None

    def test_professor_nao_pode_criar_acesso(self, client, turma, ano_letivo):
        aluno, _ = self._aluno_sem_acesso(turma, ano_letivo)
        CustomUser.objects.create_user(
            email="prof.acesso@escola.test", password="senha-forte-123", role=CustomUser.Role.PROFESSOR
        )
        client.login(username="prof.acesso@escola.test", password="senha-forte-123")

        resposta = client.post(reverse("alunos:acesso_aluno", args=[aluno.pk]), {"email": "x@exemplo.com"})

        assert resposta.status_code == 403
