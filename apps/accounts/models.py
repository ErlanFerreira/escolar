from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.core.models import TimestampedModel

from .managers import CustomUserManager


class CustomUser(AbstractUser, TimestampedModel):
    class Role(models.TextChoices):
        SECRETARIA = "SECRETARIA", "Secretaria"
        DIRETOR = "DIRETOR", "Diretor(a)"
        PROFESSOR = "PROFESSOR", "Professor(a)"
        RESPONSAVEL = "RESPONSAVEL", "Responsável"
        ALUNO = "ALUNO", "Aluno(a)"

    username = None
    email = models.EmailField("e-mail", unique=True)
    cpf = models.CharField("CPF", max_length=14, unique=True, null=True, blank=True)
    telefone = models.CharField("telefone", max_length=20, blank=True)
    foto = models.ImageField("foto", upload_to="usuarios/", null=True, blank=True)
    role = models.CharField("perfil", max_length=20, choices=Role.choices)
    must_change_password = models.BooleanField("deve trocar a senha", default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        verbose_name = "usuário"
        verbose_name_plural = "usuários"

    def __str__(self):
        return self.get_full_name() or self.email

    @property
    def is_secretaria(self):
        return self.role == self.Role.SECRETARIA

    @property
    def is_diretor(self):
        return self.role == self.Role.DIRETOR

    @property
    def is_professor(self):
        return self.role == self.Role.PROFESSOR

    @property
    def is_responsavel(self):
        return self.role == self.Role.RESPONSAVEL

    @property
    def is_aluno_role(self):
        return self.role == self.Role.ALUNO
