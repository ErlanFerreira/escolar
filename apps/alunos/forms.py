from django import forms

from apps.escola.models import Turma

from .models import Aluno, AlunoResponsavel


class AlunoForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = ["nome_completo", "data_nascimento", "cpf", "rg", "sexo", "observacoes"]
        widgets = {
            "data_nascimento": forms.DateInput(attrs={"type": "date"}),
            "observacoes": forms.Textarea(attrs={"rows": 3}),
        }


class ResponsavelForm(forms.Form):
    nome_completo = forms.CharField(label="Nome completo", max_length=255, required=False)
    cpf = forms.CharField(label="CPF", max_length=14, required=False)
    telefone = forms.CharField(label="Telefone", max_length=20, required=False)
    telefone_secundario = forms.CharField(label="Telefone secundário", max_length=20, required=False)
    email = forms.EmailField(label="E-mail", required=False)
    endereco = forms.CharField(label="Endereço", max_length=255, required=False)
    profissao = forms.CharField(label="Profissão", max_length=100, required=False)
    parentesco = forms.ChoiceField(
        label="Parentesco", choices=AlunoResponsavel.Parentesco.choices, required=False
    )
    responsavel_financeiro = forms.BooleanField(label="Responsável financeiro", required=False)
    responsavel_pedagogico = forms.BooleanField(
        label="Responsável pedagógico (recebe comunicados)", required=False, initial=True
    )
    reside_com_aluno = forms.BooleanField(label="Reside com o aluno", required=False, initial=True)

    CAMPOS_OBRIGATORIOS_SE_PREENCHIDO = ["nome_completo", "cpf", "telefone", "parentesco"]

    def clean(self):
        cleaned = super().clean()
        preenchido = any(cleaned.get(campo) for campo in ["nome_completo", "cpf", "telefone"])
        if preenchido:
            faltando = [c for c in self.CAMPOS_OBRIGATORIOS_SE_PREENCHIDO if not cleaned.get(c)]
            if faltando:
                raise forms.ValidationError(
                    "Preencha nome, CPF, telefone e parentesco para cada responsável informado, "
                    "ou deixe o formulário totalmente em branco."
                )
        return cleaned


class ResponsavelBaseFormSet(forms.BaseFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        preenchidos = [f for f in self.forms if f.cleaned_data.get("nome_completo")]
        if not preenchidos:
            raise forms.ValidationError("Informe pelo menos um responsável.")


ResponsavelFormSet = forms.formset_factory(
    ResponsavelForm, formset=ResponsavelBaseFormSet, extra=2, can_delete=False
)


class MatriculaTurmaForm(forms.Form):
    turma = forms.ModelChoiceField(
        label="Turma",
        queryset=Turma.objects.filter(ano_letivo__ativo=True).select_related("serie", "ano_letivo"),
        empty_label="Selecione a turma",
    )
