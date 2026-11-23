import pytest
from django.urls import reverse

from apps.accounts.models import CustomUser


@pytest.fixture
def usuario_com_senha_temporaria(db):
    return CustomUser.objects.create_user(
        email="novo@escola.test",
        password="TempSenha123",
        role=CustomUser.Role.RESPONSAVEL,
        must_change_password=True,
    )


@pytest.mark.django_db
class TestTrocaObrigatoriaDeSenha:
    def test_qualquer_pagina_redireciona_para_trocar_a_senha(self, client, usuario_com_senha_temporaria):
        client.login(username="novo@escola.test", password="TempSenha123")

        resposta = client.get(reverse("dashboard:responsavel"))

        assert resposta.status_code == 302
        assert resposta.url == reverse("accounts:senha_alterar")

    def test_tela_de_troca_continua_acessivel(self, client, usuario_com_senha_temporaria):
        client.login(username="novo@escola.test", password="TempSenha123")

        assert client.get(reverse("accounts:senha_alterar")).status_code == 200

    def test_trocar_a_senha_libera_o_acesso(self, client, usuario_com_senha_temporaria):
        client.login(username="novo@escola.test", password="TempSenha123")

        resposta = client.post(
            reverse("accounts:senha_alterar"),
            {
                "old_password": "TempSenha123",
                "new_password1": "UmaSenhaBemForte#2026",
                "new_password2": "UmaSenhaBemForte#2026",
            },
        )

        assert resposta.status_code == 302
        usuario_com_senha_temporaria.refresh_from_db()
        assert usuario_com_senha_temporaria.must_change_password is False
        assert usuario_com_senha_temporaria.check_password("UmaSenhaBemForte#2026")
        assert client.get(reverse("dashboard:responsavel")).status_code == 200

    def test_usuario_sem_flag_nao_e_redirecionado(self, client):
        CustomUser.objects.create_user(
            email="normal@escola.test", password="SenhaNormal123", role=CustomUser.Role.RESPONSAVEL
        )
        client.login(username="normal@escola.test", password="SenhaNormal123")

        assert client.get(reverse("dashboard:responsavel")).status_code == 200
