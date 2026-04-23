---
description: "Escribe un Dockerfile listo para producción para apps Django ejecutándose en Cloud Run usando uv como gestor de paquetes."
image: assets/social-banner.png
---

# 13 — Dockerfile

← [Anterior: 12 — Cloud Tasks y Scheduler](13_tasks.es.md)

Un Dockerfile es una receta para construir una imagen Docker. Este capítulo crea uno optimizado para Django en Cloud Run.

---

## El Dockerfile

Crea `Dockerfile` en la raíz del repo (junto a `manage.py`):

```dockerfile
# ── Base image ────────────────────────────────────────────────────────────────
FROM python:3.12-slim

# ── Install uv ───────────────────────────────────────────────────────────────
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR /app

# ── Install Python dependencies ───────────────────────────────────────────────
COPY web/pyproject.toml web/uv.lock ./
RUN uv sync --frozen --no-dev

# ── Copy application source ───────────────────────────────────────────────────
COPY web/ .

# ── Environment variables ───────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=core.settings.prod \
    PORT=8080

# ── Port ──────────────────────────────────────────────────────────────────────
EXPOSE 8080

# ── Start command ─────────────────────────────────────────────────────────────
CMD ["uv", "run", "gunicorn", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--timeout", "60", \
     "--log-file", "-", \
     "core.wsgi"]
```

---

## .dockerignore

Crea `.dockerignore` en la raíz del repo para prevenir que archivos innecesarios se envíen al contexto de build de Docker:

```
.git
web/.venv
web/media/
web/staticfiles/
web/htmlcov/
**/__pycache__
**/*.pyc
**/*.pyo
.env
*.md
DEPLOY/
```

Esto mantiene la imagen pequeña y previene que secretos se incluyan accidentalmente.

---

## Opciones de Gunicorn explicadas

| Opción | Valor | Por qué |
|---|---|---|
| `--bind 0.0.0.0:8080` | Escuchar en todas las interfaces, puerto 8080 | Cloud Run espera el puerto 8080 |
| `--workers 2` | 2 procesos worker | Manejar solicitudes concurrentes |
| `--timeout 60` | 60 segundos de timeout | Matar solicitudes lentas para prevenir bloqueo |
| `--log-file -` | Escribir logs a stdout | Cloud Logging captura stdout |
| `core.wsgi` | Punto de entrada WSGI | Located at `web/core/wsgi.py` |

---

## Construir y probar localmente

Construir la imagen:

```bash
docker build -t mycoolproject-app .
```

Probarla localmente (requiere un Postgres local o mock DATABASE_URL):

```bash
docker run --rm \
  -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/mycoolproject_dev" \
  -e SECRET_KEY="local-test-key" \
  -e ALLOWED_HOSTS="localhost" \
  -p 8080:8080 \
  mycoolproject-app
```

Visita `http://localhost:8080` para verificar que inicia.

---

## El nombre de la imagen

En `main.tf`, el servicio Cloud Run referencia la imagen:

```hcl
image = "${google_artifact_registry_repository.app.repository_url}/app:latest"
```

Esto se resuelve a:
```
southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:latest
```

GitHub Actions hará push de imágenes con:
- Etiqueta `latest` — siempre apunta al build más reciente
- Etiqueta `<git-sha>` — única por commit, para rollbacks

---

## Build de dos etapas (opcional)

Para imágenes más pequeñas, puedes usar un build de dos etapas:

```dockerfile
# Stage 1: Build
FROM python:3.12-slim as builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/
WORKDIR /app
COPY web/pyproject.toml web/uv.lock ./
RUN uv sync --frozen --no-dev
COPY web/ .

# Stage 2: Runtime
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/web/ ./web/
COPY --from=builder /app/.venv/ ./.venv/
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=core.settings.prod \
    PORT=8080
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "60", "--log-file", "-", "core.wsgi"]
```

Esto resulta en una imagen más pequeña porque excluye las herramientas de build. Por simplicidad, usamos la versión de una etapa en esta guía.

---

## Navegación



- [01 — Introducción: Qué vamos a construir](01_introduction.es.md)
- [02 — Visión general de Terraform](02_terraform_overview.es.md)
- [03 — Servicios en la nube explicados](03_cloud_services.es.md)
- [04 — Base de datos PlanetScale explicada](04_planetscale.es.md)
- [05 — Configuración del proyecto y estado de Terraform](05_project_setup.es.md)
- [06 — Proyecto GCP y APIs](06_gcp_project.es.md)
- [07 — Artifact Registry](07_artifact_registry.es.md)
- [08 — Gestión de Secretos](09_secrets.es.md)
- [09 — Cloud Storage](10_storage.es.md)
- [10 — Service Accounts e IAM](11_iam.es.md)
- [11 — Cloud Run](12_cloud_run.es.md)
- [12 — Cloud Tasks y Scheduler](13_tasks.es.md)
- 13 — Dockerfile (Capítulo actual)
- [14 — Primer Despliegue](15_first_deploy.es.md)
- [15 — Dominio personalizado y SSL](16_domain_ssl.es.md)
- [16 — Workload Identity Federation](17_wif.es.md)
- [17 — GitHub Actions CI/CD](18_github_actions.es.md)
- [18 — Referencia Rápida](19_quick_reference.es.md)
