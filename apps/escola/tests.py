import pytest
from django.core.exceptions import ValidationError

from apps.escola.models import AnoLetivo


@pytest.mark.django_db
class TestAnoLetivo:
    def test_only_one_ano_letivo_can_be_active(self):
        AnoLetivo.objects.create(ano=2025, data_inicio="2025-02-01", data_fim="2025-12-15", ativo=True)
        segundo = AnoLetivo(ano=2026, data_inicio="2026-02-02", data_fim="2026-12-18", ativo=True)

        with pytest.raises(ValidationError):
            segundo.full_clean()

    def test_data_fim_must_be_after_data_inicio(self):
        ano_letivo = AnoLetivo(ano=2026, data_inicio="2026-12-18", data_fim="2026-02-02")

        with pytest.raises(ValidationError):
            ano_letivo.full_clean()
