from django.forms import modelformset_factory

from .models import PresencaAluno

PresencaFormSet = modelformset_factory(PresencaAluno, fields=["status", "observacao"], extra=0)
