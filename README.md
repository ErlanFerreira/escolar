# Gestão Escolar

Sistema de gestão escolar (matrícula, notas, frequência, financeiro e comunicação) para secretaria, professores, responsáveis e alunos.

## Stack

- Python + Django 6.1 + PostgreSQL (Neon)
- Django templates + HTMX + Bootstrap 5 (sem SPA separada)

## Setup local

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements/dev.txt
copy .env.example .env   # depois preencher SECRET_KEY e DATABASE_URL
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Testes

```bash
pytest
```

## Estrutura

Cada módulo funcional vive em `apps/<nome>` (accounts, escola, professores, alunos, notas, frequencia, financeiro, comunicacao, dashboard). Veja o histórico de commits e o plano de marcos (M0–M9) para o roteiro de construção.

## E-mail (recuperação de senha) em produção

O plano gratuito do Render bloqueia SMTP (portas 25/465/587), então o envio usa a API HTTPS do [Brevo](https://www.brevo.com) (plano gratuito: 300 e-mails/dia).

1. Crie uma conta no Brevo e, em *Senders, Domains & Dedicated IPs → Senders*, cadastre e **verifique** o e-mail remetente (o Brevo manda um link de confirmação para ele).
2. Em *SMTP & API → API Keys*, gere uma chave de API (começa com `xkeysib-`).
3. No Render, em *Environment* do serviço, defina:
   - `BREVO_API_KEY`: a chave gerada.
   - `DEFAULT_FROM_EMAIL`: `Gestão Escolar <remetente-verificado@exemplo.com>` (tem que ser o remetente verificado no passo 1).
4. Salve; o serviço reinicia. Teste em `/senha/resetar/` com o e-mail de uma conta existente.

Sem `BREVO_API_KEY`, os e-mails só aparecem no log do serviço (nada é entregue). Sem domínio próprio, e-mails de remetente Gmail/Outlook podem cair no spam; para entregabilidade melhor, use um remetente de domínio próprio autenticado no Brevo.

## Deploy (Render)

O repositório já tem um `render.yaml` (Blueprint) pronto. Passos:

1. Suba o código para um repositório no GitHub/GitLab (o Render faz deploy a partir de um repo remoto, não de arquivos locais).
2. No painel do Render, "New" → "Blueprint" → aponte para o repositório. Ele lê o `render.yaml` automaticamente.
3. Antes do primeiro deploy, preencha manualmente (o blueprint marca essas variáveis como `sync: false`, ou seja, não preenche sozinho):
   - `DATABASE_URL`: a connection string do Neon (a mesma usada localmente).
   - `ALLOWED_HOSTS`: o domínio que o Render atribuir, ex. `gestao-escolar.onrender.com`.
   - `CSRF_TRUSTED_ORIGINS`: o mesmo domínio, com esquema — `https://gestao-escolar.onrender.com`.
   - `SECRET_KEY` já é gerado automaticamente pelo blueprint.
4. O build roda `collectstatic` e `migrate` automaticamente (ver `render.yaml`).

**Limitação do plano gratuito a ter em mente:** o disco é efêmero — qualquer arquivo enviado por upload (fotos de aluno, anexos de comunicado, logo da escola) é perdido a cada novo deploy ou reinício do serviço. Para uploads persistentes de verdade, será necessário migrar `MEDIA_ROOT` para um storage externo (S3, Cloudinary, etc.) — não implementado ainda, por não ser necessário para validar o MVP. O serviço também "dorme" após um tempo sem acesso (cold start na primeira requisição seguinte), padrão do free tier do Render.
