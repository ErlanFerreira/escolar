import pytest
from django.urls import reverse

from apps.accounts.models import CustomUser


@pytest.mark.django_db
class TestCustomUserManager:
    def test_create_user_sets_role_and_hashes_password(self):
        user = CustomUser.objects.create_user(
            email="prof@escola.test", password="senha-forte-123", role=CustomUser.Role.PROFESSOR
        )
        assert user.email == "prof@escola.test"
        assert user.role == CustomUser.Role.PROFESSOR
        assert user.check_password("senha-forte-123")
        assert user.is_professor
        assert not user.is_secretaria

    def test_create_superuser_defaults_to_secretaria_role(self):
        admin = CustomUser.objects.create_superuser(email="admin@escola.test", password="senha-forte-123")
        assert admin.is_staff
        assert admin.is_superuser
        assert admin.role == CustomUser.Role.SECRETARIA


@pytest.mark.django_db
class TestPostLoginRedirect:
    @pytest.mark.parametrize(
        "role,expected_url_name",
        [
            (CustomUser.Role.SECRETARIA, "dashboard:secretaria"),
            (CustomUser.Role.PROFESSOR, "dashboard:professor"),
            (CustomUser.Role.RESPONSAVEL, "dashboard:responsavel"),
            (CustomUser.Role.ALUNO, "dashboard:aluno"),
        ],
    )
    def test_redirects_each_role_to_its_own_dashboard(self, client, role, expected_url_name):
        email = f"{role.lower()}@escola.test"
        CustomUser.objects.create_user(email=email, password="senha-forte-123", role=role)
        client.login(username=email, password="senha-forte-123")

        response = client.get(reverse("accounts:post_login_redirect"))

        assert response.url == reverse(expected_url_name)

    def test_role_required_mixin_blocks_other_roles(self, client):
        CustomUser.objects.create_user(
            email="professor@escola.test", password="senha-forte-123", role=CustomUser.Role.PROFESSOR
        )
        client.login(username="professor@escola.test", password="senha-forte-123")

        response = client.get(reverse("dashboard:secretaria"))

        assert response.status_code == 403
