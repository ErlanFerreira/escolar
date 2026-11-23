from .base import *  # noqa: F403
from .base import env

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# Render (e a maioria dos PaaS) terminam TLS no proxy e repassam a requisição
# em HTTP puro internamente — sem isso, SECURE_SSL_REDIRECT gera loop infinito
# de redirecionamento, pois o Django acha que toda requisição chegou insegura.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

# O plano gratuito do Render bloqueia SMTP (portas 25/465/587), então o envio é por API HTTPS (Brevo).
# Sem BREVO_API_KEY os e-mails vão só para o log (console) — nada é entregue, mas nada quebra.
BREVO_API_KEY = env("BREVO_API_KEY", default="")
if BREVO_API_KEY:
    EMAIL_BACKEND = "anymail.backends.brevo.EmailBackend"
    ANYMAIL = {"BREVO_API_KEY": BREVO_API_KEY}
else:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
