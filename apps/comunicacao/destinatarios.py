from apps.accounts.models import CustomUser
from apps.alunos.models import AlunoResponsavel, Matricula
from apps.professores.models import ProfessorDisciplinaTurma

from .models import Comunicado


def calcular_destinatarios(comunicado):
    """CustomUser ativos que devem ver este comunicado — usado para relatório de leitura."""
    PublicoAlvo = Comunicado.PublicoAlvo
    turmas = comunicado.turmas.all()

    if comunicado.publico_alvo == PublicoAlvo.PROFESSORES:
        return CustomUser.objects.filter(role=CustomUser.Role.PROFESSOR, is_active=True)

    if comunicado.publico_alvo == PublicoAlvo.RESPONSAVEIS:
        qs = CustomUser.objects.filter(role=CustomUser.Role.RESPONSAVEL, is_active=True)
        if turmas.exists():
            aluno_ids = Matricula.objects.filter(turma__in=turmas, status=Matricula.Status.ATIVA).values_list(
                "aluno_id", flat=True
            )
            resp_user_ids = AlunoResponsavel.objects.filter(
                aluno_id__in=aluno_ids, responsavel_pedagogico=True
            ).values_list("responsavel__user_id", flat=True)
            qs = qs.filter(pk__in=resp_user_ids)
        return qs

    if comunicado.publico_alvo == PublicoAlvo.TURMA_ESPECIFICA:
        aluno_ids = Matricula.objects.filter(turma__in=turmas, status=Matricula.Status.ATIVA).values_list(
            "aluno_id", flat=True
        )
        aluno_user_ids = set(CustomUser.objects.filter(aluno__pk__in=aluno_ids).values_list("pk", flat=True))
        resp_user_ids = set(
            AlunoResponsavel.objects.filter(aluno_id__in=aluno_ids, responsavel_pedagogico=True).values_list(
                "responsavel__user_id", flat=True
            )
        )
        prof_user_ids = set(
            ProfessorDisciplinaTurma.objects.filter(turma__in=turmas).values_list(
                "professor__user_id", flat=True
            )
        )
        ids = aluno_user_ids | resp_user_ids | prof_user_ids
        return CustomUser.objects.filter(pk__in=ids, is_active=True)

    return CustomUser.objects.filter(is_active=True)
