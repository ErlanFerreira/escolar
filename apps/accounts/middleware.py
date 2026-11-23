from django.shortcuts import redirect
from django.urls import reverse


class ForcePasswordChangeMiddleware:
    """Enquanto ``must_change_password`` estiver ativo, só libera a troca de senha e o logout."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and user.must_change_password:
            liberadas = {reverse("accounts:senha_alterar"), reverse("accounts:logout")}
            if request.path not in liberadas and not request.path.startswith("/static/"):
                return redirect("accounts:senha_alterar")
        return self.get_response(request)
