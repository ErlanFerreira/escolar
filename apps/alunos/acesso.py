from apps.accounts.models import CustomUser
from apps.accounts.services import criar_usuario_de_acesso, email_em_uso


def _resultado(perfil, nome, email, senha=None, aviso=None):
    return {"perfil": perfil, "nome": nome, "email": email, "senha": senha, "aviso": aviso}


def criar_acesso_responsavel(responsavel, email):
    """Cria e vincula o login do responsável. Devolve um dict para exibir à secretaria."""
    if responsavel.user_id:
        return _resultado(
            "Responsável", responsavel.nome_completo, responsavel.user.email, aviso="já possui acesso"
        )
    if not email:
        return None
    if email_em_uso(email):
        return _resultado(
            "Responsável",
            responsavel.nome_completo,
            email,
            aviso="e-mail já usado por outra conta, acesso não criado",
        )
    usuario, senha = criar_usuario_de_acesso(
        email=email, nome_completo=responsavel.nome_completo, role=CustomUser.Role.RESPONSAVEL
    )
    responsavel.user = usuario
    if not responsavel.email:
        responsavel.email = email
    responsavel.save(update_fields=["user", "email"])
    return _resultado("Responsável", responsavel.nome_completo, email, senha=senha)


def criar_acesso_aluno(aluno, email):
    if aluno.user_id:
        return _resultado("Aluno", aluno.nome_completo, aluno.user.email, aviso="já possui acesso")
    if not email:
        return None
    if email_em_uso(email):
        return _resultado(
            "Aluno", aluno.nome_completo, email, aviso="e-mail já usado por outra conta, acesso não criado"
        )
    usuario, senha = criar_usuario_de_acesso(
        email=email, nome_completo=aluno.nome_completo, role=CustomUser.Role.ALUNO
    )
    aluno.user = usuario
    aluno.save(update_fields=["user"])
    return _resultado("Aluno", aluno.nome_completo, email, senha=senha)
