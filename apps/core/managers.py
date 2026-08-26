"""
Shared pattern for role-scoped querysets: every app whose data must be
filtered per logged-in user (Turma, Aluno, Nota, Frequencia, Cobranca, ...)
defines a queryset that implements ``for_user``, and exposes it as the
model's default manager via ``as_manager()``.

Subclasses must implement ``for_user`` for each accounts.CustomUser.Role.
Keeping the branching here (instead of in views) means the same scoping
logic protects the Django admin, regular views, and any future API.
"""

from django.db import models


class RoleScopedQuerySet(models.QuerySet):
    def for_user(self, user):
        """Return only the rows ``user`` is allowed to see, by role.

        Must be implemented by each concrete queryset subclass.
        """
        raise NotImplementedError
