from apps.accounts.models import CustomUser
from apps.core.managers import RoleScopedQuerySet


class TurmaQuerySet(RoleScopedQuerySet):
    def for_user(self, user):
        Role = CustomUser.Role
        if user.role in (Role.SECRETARIA, Role.DIRETOR):
            return self.all()
        if user.role == Role.PROFESSOR:
            from apps.professores.models import ProfessorDisciplinaTurma

            turma_ids = ProfessorDisciplinaTurma.objects.filter(professor__user=user).values_list(
                "turma_id", flat=True
            )
            return self.filter(pk__in=turma_ids).distinct()
        if user.role in (Role.RESPONSAVEL, Role.ALUNO):
            from apps.alunos.models import Matricula

            turma_ids = Matricula.objects.for_user(user).values_list("turma_id", flat=True)
            return self.filter(pk__in=turma_ids).distinct()
        return self.none()
