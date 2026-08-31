from django.db.models import Q

from apps.accounts.models import CustomUser
from apps.core.managers import RoleScopedQuerySet


class ComunicadoQuerySet(RoleScopedQuerySet):
    def for_user(self, user):
        from apps.escola.models import Turma

        Role = CustomUser.Role
        PublicoAlvo = self.model.PublicoAlvo

        if user.role in (Role.SECRETARIA, Role.DIRETOR):
            return self.all()

        turma_ids = list(Turma.objects.for_user(user).values_list("pk", flat=True))

        if user.role == Role.PROFESSOR:
            return self.filter(
                Q(publico_alvo=PublicoAlvo.TODOS)
                | Q(publico_alvo=PublicoAlvo.PROFESSORES)
                | Q(publico_alvo=PublicoAlvo.TURMA_ESPECIFICA, turmas__in=turma_ids)
            ).distinct()

        if user.role == Role.RESPONSAVEL:
            return self.filter(
                Q(publico_alvo=PublicoAlvo.TODOS)
                | Q(publico_alvo=PublicoAlvo.RESPONSAVEIS, turmas__isnull=True)
                | Q(publico_alvo=PublicoAlvo.RESPONSAVEIS, turmas__in=turma_ids)
                | Q(publico_alvo=PublicoAlvo.TURMA_ESPECIFICA, turmas__in=turma_ids)
            ).distinct()

        if user.role == Role.ALUNO:
            return self.filter(
                Q(publico_alvo=PublicoAlvo.TODOS)
                | Q(publico_alvo=PublicoAlvo.TURMA_ESPECIFICA, turmas__in=turma_ids)
            ).distinct()

        return self.none()
