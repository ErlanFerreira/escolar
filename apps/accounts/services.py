import secrets
import string

from .models import CustomUser

ALFABETO_SENHA = string.ascii_letters + string.digits


def gerar_senha_temporaria(tamanho=12):
    return "".join(secrets.choice(ALFABETO_SENHA) for _ in range(tamanho))


def email_em_uso(email):
    return CustomUser.objects.filter(email__iexact=email).exists()


def criar_usuario_de_acesso(*, email, nome_completo, role):
    """Cria o login com senha temporária (troca obrigatória no primeiro acesso).

    Retorna ``(usuario, senha_temporaria)``. A senha só existe em texto puro aqui:
    quem chama deve repassá-la uma única vez à secretaria, sem persistir.
    """
    primeiro_nome, _, sobrenome = nome_completo.strip().partition(" ")
    senha = gerar_senha_temporaria()
    usuario = CustomUser.objects.create_user(
        email=email,
        password=senha,
        role=role,
        first_name=primeiro_nome,
        last_name=sobrenome,
        must_change_password=True,
    )
    return usuario, senha
