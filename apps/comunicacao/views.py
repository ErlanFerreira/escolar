from django.urls import reverse
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView

from apps.accounts.models import CustomUser
from apps.core.mixins import RoleRequiredMixin

from .destinatarios import calcular_destinatarios
from .forms import ComunicadoForm
from .models import Comunicado, ComunicadoLeitura

TODOS_OS_PERFIS = (
    CustomUser.Role.SECRETARIA,
    CustomUser.Role.DIRETOR,
    CustomUser.Role.PROFESSOR,
    CustomUser.Role.RESPONSAVEL,
    CustomUser.Role.ALUNO,
)


class ComunicadoListView(RoleRequiredMixin, ListView):
    allowed_roles = TODOS_OS_PERFIS
    template_name = "comunicacao/lista.html"
    context_object_name = "comunicados"

    def get_queryset(self):
        return (
            Comunicado.objects.for_user(self.request.user).select_related("autor").prefetch_related("turmas")
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lidos_ids"] = set(
            ComunicadoLeitura.objects.filter(user=self.request.user, lida_em__isnull=False).values_list(
                "comunicado_id", flat=True
            )
        )
        return context


class ComunicadoDetailView(RoleRequiredMixin, DetailView):
    allowed_roles = TODOS_OS_PERFIS
    model = Comunicado
    template_name = "comunicacao/detalhe.html"
    context_object_name = "comunicado"

    def get_queryset(self):
        return Comunicado.objects.for_user(self.request.user).prefetch_related("turmas")

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        ComunicadoLeitura.objects.update_or_create(
            comunicado=self.object, user=request.user, defaults={"lida_em": timezone.now()}
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.role in (CustomUser.Role.SECRETARIA, CustomUser.Role.DIRETOR):
            destinatarios = calcular_destinatarios(self.object)
            context["total_destinatarios"] = destinatarios.count()
            context["total_leram"] = ComunicadoLeitura.objects.filter(
                comunicado=self.object, lida_em__isnull=False, user__in=destinatarios
            ).count()
        return context


class ComunicadoCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (CustomUser.Role.SECRETARIA, CustomUser.Role.DIRETOR)
    model = Comunicado
    form_class = ComunicadoForm
    template_name = "comunicacao/form.html"

    def form_valid(self, form):
        form.instance.autor = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("comunicacao:detalhe", args=[self.object.pk])
