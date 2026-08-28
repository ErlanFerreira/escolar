from apps.accounts.models import CustomUser
from apps.core.managers import RoleScopedQuerySet


class AulaQuerySet(RoleScopedQuerySet):
    def for_user(self, user):
        Role = CustomUser.Role
        if user.role in (Role.SECRETARIA, Role.DIRETOR):
            return self.all()
        if user.role == Role.PROFESSOR:
            return self.filter(professor__user=user)
        if user.role in (Role.RESPONSAVEL, Role.ALUNO):
            from apps.escola.models import Turma

            turma_ids = Turma.objects.for_user(user).values_list("pk", flat=True)
            return self.filter(turma_id__in=turma_ids)
        return self.none()


class PresencaAlunoQuerySet(RoleScopedQuerySet):
    def for_user(self, user):
        Role = CustomUser.Role
        if user.role in (Role.SECRETARIA, Role.DIRETOR):
            return self.all()
        if user.role == Role.PROFESSOR:
            return self.filter(aula__professor__user=user)
        if user.role == Role.RESPONSAVEL:
            from apps.alunos.models import Aluno

            aluno_ids = Aluno.objects.for_user(user).values_list("pk", flat=True)
            return self.filter(aluno_id__in=aluno_ids)
        if user.role == Role.ALUNO:
            return self.filter(aluno__user=user)
        return self.none()
