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
