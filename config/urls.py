from django.conf import settings
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.accounts.urls")),
    path("", include("apps.dashboard.urls")),
    path("", include("apps.alunos.urls")),
    path("", include("apps.notas.urls")),
    path("", include("apps.frequencia.urls")),
    path("", include("apps.financeiro.urls")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]
