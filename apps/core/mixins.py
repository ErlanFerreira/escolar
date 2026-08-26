from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied


class RoleRequiredMixin(LoginRequiredMixin):
    """Restrict a class-based view to specific ``CustomUser.Role`` values.

    Usage: set ``allowed_roles = (CustomUser.Role.PROFESSOR, ...)`` on the view.
    """

    allowed_roles: tuple[str, ...] = ()

    def dispatch(self, request, *args, **kwargs):
        role_ok = not self.allowed_roles or request.user.role in self.allowed_roles
        if request.user.is_authenticated and not role_ok:
            raise PermissionDenied("Você não tem permissão para acessar esta página.")
        return super().dispatch(request, *args, **kwargs)
