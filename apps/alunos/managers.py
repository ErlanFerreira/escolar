from apps.accounts.models import CustomUser
from apps.core.managers import RoleScopedQuerySet


class AlunoQuerySet(RoleScopedQuerySet):
    def for_user(self, user):
        Role = CustomUser.Role
        if user.role in (Role.SECRETARIA, Role.DIRETOR):
            return self.all()
        if user.role == Role.PROFESSOR:
            from apps.escola.models import Turma

            turmas_ids = Turma.objects.for_user(user).values_list("pk", flat=True)
            return self.filter(matriculas__turma_id__in=turmas_ids).distinct()
        if user.role == Role.RESPONSAVEL:
            return self.filter(responsaveis__responsavel__user=user).distinct()
        if user.role == Role.ALUNO:
            return self.filter(user=user)
        return self.none()


class MatriculaQuerySet(RoleScopedQuerySet):
    def for_user(self, user):
        Role = CustomUser.Role
        if user.role in (Role.SECRETARIA, Role.DIRETOR):
            return self.all()
        if user.role == Role.PROFESSOR:
            from apps.escola.models import Turma

            turmas_ids = Turma.objects.for_user(user).values_list("pk", flat=True)
            return self.filter(turma_id__in=turmas_ids)
        if user.role == Role.RESPONSAVEL:
            return self.filter(aluno__responsaveis__responsavel__user=user).distinct()
        if user.role == Role.ALUNO:
            return self.filter(aluno__user=user)
        return self.none()
