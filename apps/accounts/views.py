from django.contrib.auth import views as auth_views
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.views import View

from .forms import EmailAuthenticationForm
from .models import CustomUser

ROLE_DASHBOARD_URL_NAME = {
    CustomUser.Role.SECRETARIA: "dashboard:secretaria",
    CustomUser.Role.DIRETOR: "dashboard:secretaria",
    CustomUser.Role.PROFESSOR: "dashboard:professor",
    CustomUser.Role.RESPONSAVEL: "dashboard:responsavel",
    CustomUser.Role.ALUNO: "dashboard:aluno",
}


class LoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    authentication_form = EmailAuthenticationForm
    redirect_authenticated_user = True


class LogoutView(auth_views.LogoutView):
    pass


class PostLoginRedirectView(LoginRequiredMixin, View):
    """Sends a freshly logged-in user to the home page for their role."""

    def get(self, request, *args, **kwargs):
        url_name = ROLE_DASHBOARD_URL_NAME.get(request.user.role, "accounts:login")
        return redirect(url_name)
