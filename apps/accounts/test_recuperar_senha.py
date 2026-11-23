import json
import re
from unittest import mock

import pytest
from django.core import mail
from django.urls import reverse

from apps.accounts.models import CustomUser


@pytest.fixture
def usuario(db):
    return CustomUser.objects.create_user(
        email="esqueci@escola.test", password="SenhaAntiga123", role=CustomUser.Role.RESPONSAVEL
    )


@pytest.mark.django_db
class TestRecuperarSenha:
    def test_fluxo_completo_envia_email_e_permite_definir_nova_senha(self, client, usuario):
        resposta = client.post(reverse("accounts:password_reset"), {"email": "esqueci@escola.test"})

        assert resposta.status_code == 302
        assert resposta.url == reverse("accounts:password_reset_done")
        assert len(mail.outbox) == 1
        mensagem = mail.outbox[0]
        assert mensagem.to == ["esqueci@escola.test"]
        assert "Gestão Escolar" in mensagem.subject

        link = re.search(r"http://testserver(/senha/resetar/confirmar/\S+)", mensagem.body).group(1)
        resposta = client.get(link, follow=True)
        assert resposta.status_code == 200

        formulario_url = resposta.redirect_chain[-1][0]
        resposta = client.post(
            formulario_url,
            {"new_password1": "NovaSenhaBemForte#2026", "new_password2": "NovaSenhaBemForte#2026"},
        )
        assert resposta.status_code == 302
        assert resposta.url == reverse("accounts:password_reset_complete")

        usuario.refresh_from_db()
        assert usuario.check_password("NovaSenhaBemForte#2026")

    def test_email_desconhecido_nao_envia_nada_e_nao_revela_que_nao_existe(self, client, db):
        resposta = client.post(reverse("accounts:password_reset"), {"email": "ninguem@escola.test"})

        assert resposta.status_code == 302
        assert resposta.url == reverse("accounts:password_reset_done")
        assert mail.outbox == []

    def test_em_producao_o_email_sai_pela_api_do_brevo(self, client, usuario, settings):
        settings.EMAIL_BACKEND = "anymail.backends.brevo.EmailBackend"
        settings.ANYMAIL = {"BREVO_API_KEY": "xkeysib-fake"}
        settings.DEFAULT_FROM_EMAIL = "Gestão Escolar <remetente@exemplo.com>"
        resposta_api = mock.Mock(status_code=201, content=b'{"messageId": "<abc@brevo>"}', text="{}")
        resposta_api.json.return_value = {"messageId": "<abc@brevo>"}

        with mock.patch("requests.Session.request", return_value=resposta_api) as chamada:
            client.post(reverse("accounts:password_reset"), {"email": "esqueci@escola.test"})

        kwargs = chamada.call_args.kwargs
        assert kwargs["url"] == "https://api.brevo.com/v3/smtp/email"
        assert kwargs["headers"]["api-key"] == "xkeysib-fake"
        corpo = json.loads(kwargs["data"])
        assert corpo["sender"] == {"email": "remetente@exemplo.com", "name": "Gestão Escolar"}
        assert corpo["to"] == [{"email": "esqueci@escola.test"}]
