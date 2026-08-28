from apps.accounts.models import CustomUser
from apps.core.managers import RoleScopedQuerySet


class CobrancaQuerySet(RoleScopedQuerySet):
    def for_user(self, user):
        Role = CustomUser.Role
        if user.role in (Role.SECRETARIA, Role.DIRETOR):
            return self.all()
        if user.role == Role.RESPONSAVEL:
            return self.filter(responsavel_financeiro__user=user)
        return self.none()
