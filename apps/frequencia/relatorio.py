from .models import PresencaAluno


def calcular_frequencia(aluno):
    """Agrupa as presenças do aluno por disciplina e calcula o % de presença.

    Falta justificada não conta como presença no percentual (MVP:
    só ``PRESENTE`` conta a favor do aluno).
    """
    presencas = (
        PresencaAluno.objects.filter(aluno=aluno)
        .select_related("aula__disciplina")
        .order_by("aula__disciplina__nome", "aula__data")
    )

    por_disciplina = {}
    for presenca in presencas:
        disciplina = presenca.aula.disciplina
        por_disciplina.setdefault(disciplina, []).append(presenca)

    resumo = []
    for disciplina, lista in por_disciplina.items():
        total = len(lista)
        presentes = sum(1 for p in lista if p.status == PresencaAluno.Status.PRESENTE)
        percentual = (presentes / total * 100) if total else None
        resumo.append(
            {
                "disciplina": disciplina,
                "total": total,
                "presentes": presentes,
                "percentual": percentual,
                "presencas": lista,
            }
        )

    resumo.sort(key=lambda item: item["disciplina"].nome)
    return resumo
