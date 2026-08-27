from .models import Nota


def montar_boletim(aluno):
    """Agrupa as notas lançadas do aluno por disciplina e calcula a média ponderada pelo peso da avaliação."""
    notas = (
        Nota.objects.filter(aluno=aluno, valor__isnull=False)
        .select_related("avaliacao__disciplina", "avaliacao__periodo")
        .order_by("avaliacao__disciplina__nome", "avaliacao__periodo__numero", "avaliacao__data")
    )

    por_disciplina = {}
    for nota in notas:
        disciplina = nota.avaliacao.disciplina
        por_disciplina.setdefault(disciplina, []).append(nota)

    boletim = []
    for disciplina, lista_notas in por_disciplina.items():
        soma_ponderada = sum(n.valor * n.avaliacao.peso for n in lista_notas)
        soma_pesos = sum(n.avaliacao.peso for n in lista_notas)
        media = soma_ponderada / soma_pesos if soma_pesos else None
        boletim.append({"disciplina": disciplina, "notas": lista_notas, "media": media})

    boletim.sort(key=lambda item: item["disciplina"].nome)
    return boletim
