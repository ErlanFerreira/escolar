from datetime import date

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, FormView, ListView, TemplateView

from apps.accounts.models import CustomUser
from apps.core.mixins import RoleRequiredMixin

from .forms import GerarCobrancasForm, PagamentoForm
from .models import Cobranca
from .services import gerar_cobrancas_para_plano


class CobrancaListView(RoleRequiredMixin, ListView):
    allowed_roles = (CustomUser.Role.SECRETARIA, CustomUser.Role.DIRETOR)
    template_name = "financeiro/lista.html"
    context_object_name = "cobrancas"
    paginate_by = 50

    def get_queryset(self):
        return (
            Cobranca.objects.for_user(self.request.user)
            .select_related("aluno", "plano", "pagamento")
            .order_by("-data_vencimento")
        )


class GerarCobrancasView(RoleRequiredMixin, FormView):
    allowed_roles = (CustomUser.Role.SECRETARIA, CustomUser.Role.DIRETOR)
    form_class = GerarCobrancasForm
    template_name = "financeiro/gerar.html"
    success_url = reverse_lazy("financeiro:lista")

    def form_valid(self, form):
        criadas = gerar_cobrancas_para_plano(form.cleaned_data["plano"])
        messages.success(self.request, f"{criadas} cobrança(s) gerada(s) com sucesso.")
        return super().form_valid(form)


class InadimplenciaView(RoleRequiredMixin, TemplateView):
    allowed_roles = (CustomUser.Role.SECRETARIA, CustomUser.Role.DIRETOR)
    template_name = "financeiro/inadimplencia.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cobrancas = list(
            Cobranca.objects.filter(status=Cobranca.Status.PENDENTE, data_vencimento__lt=date.today())
            .select_related("aluno", "responsavel_financeiro")
            .order_by("data_vencimento")
        )
        context["cobrancas"] = cobrancas
        context["total"] = sum((c.valor_final for c in cobrancas), start=0)
        return context


class RegistrarPagamentoView(RoleRequiredMixin, CreateView):
    allowed_roles = (CustomUser.Role.SECRETARIA, CustomUser.Role.DIRETOR)
    form_class = PagamentoForm
    template_name = "financeiro/pagamento_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.cobranca = get_object_or_404(Cobranca.objects.for_user(request.user), pk=kwargs["cobranca_id"])
        if self.cobranca.status == Cobranca.Status.PAGO:
            messages.info(request, "Essa cobrança já está paga.")
            return redirect("financeiro:lista")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cobranca"] = self.cobranca
        return context

    def form_valid(self, form):
        form.instance.cobranca = self.cobranca
        form.instance.registrado_por = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, "Pagamento registrado com sucesso.")
        return response

    def get_success_url(self):
        return reverse("financeiro:lista")


class MinhasCobrancasView(RoleRequiredMixin, ListView):
    allowed_roles = (CustomUser.Role.RESPONSAVEL,)
    template_name = "financeiro/minhas_cobrancas.html"
    context_object_name = "cobrancas"

    def get_queryset(self):
        return (
            Cobranca.objects.for_user(self.request.user)
            .select_related("aluno", "plano")
            .order_by("-data_vencimento")
        )
