from .models import Comunicado, ComunicadoLeitura


def contar_nao_lidos(user):
    comunicados_ids = set(Comunicado.objects.for_user(user).values_list("pk", flat=True))
    lidos_ids = set(
        ComunicadoLeitura.objects.filter(user=user, lida_em__isnull=False).values_list(
            "comunicado_id", flat=True
        )
    )
    return len(comunicados_ids - lidos_ids)
