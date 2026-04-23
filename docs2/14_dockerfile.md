---
description: "Write a production-ready Dockerfile for Django apps running on Cloud Run using uv as the package manager."
image: assets/social-banner.png
---

# 14 — Dockerfile

← [Previous: 13 — Cloud Tasks & Scheduler](13_tasks.md)

A Dockerfile is a recipe for building a Docker image. This chapter creates one optimized for Django on Cloud Run.

---

## The Dockerfile

Create `Dockerfile` at the repo root (next to `manage.py`):

```dockerfile
# ── Base image ────────────────────────────────────────────────────────────────
# python:3.12-slim is a minimal Debian image with Python 3.12.
# "slim" means no build tools, compilers, or docs — smaller image size.
FROM python:3.12-slim

# ── Install uv ───────────────────────────────────────────────────────────────
# uv is a fast Python package manager (much faster than pip).
# We copy the uv binary from the official Docker image rather than installing it.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# ── Working directory ─────────────────────────────────────────────────────────
# All subsequent commands run from /app inside the container.
WORKDIR /app

# ── Install Python dependencies ───────────────────────────────────────────────
# Copy only the dependency files first (not the full source).
# Docker caches each layer — if pyproject.toml and uv.lock haven't changed,
# this layer is reused on the next build, making builds much faster.
COPY web/pyproject.toml web/uv.lock ./
RUN uv sync --frozen --no-dev
# --frozen: fail if uv.lock is out of date (ensures reproducible builds)
# --no-dev: skip dev-only dependencies (django_extensions, test tools, etc.)

# ── Copy application source ───────────────────────────────────────────────────
# Copied after dependency install so code changes don't invalidate the dep cache.
COPY web/ .

# ── Environment variables ───────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=core.settings.prod \
    PORT=8080
# PYTHONDONTWRITEBYTECODE: don't write .pyc files (unnecessary in containers)
# PYTHONUNBUFFERED: flush stdout/stderr immediately (so logs appear in real time)
# DJANGO_SETTINGS_MODULE: tells Django to use prod.py settings
# PORT: Cloud Run injects this; Gunicorn reads it

# ── Port ──────────────────────────────────────────────────────────────────────
EXPOSE 8080

# ── Start command ─────────────────────────────────────────────────────────────
# Gunicorn is a production-grade WSGI server. It runs Django's wsgi.py application.
# Django's built-in dev server (manage.py runserver) must NEVER be used in prod.
CMD ["uv", "run", "gunicorn", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--timeout", "60", \
     "--log-file", "-", \
     "core.wsgi"]
```

---

## .dockerignore

Create `.dockerignore` at the repo root to prevent unnecessary files from being sent to the Docker build context:

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

This keeps the image small and prevents secrets from being accidentally included.

---

## Gunicorn options explained

| Option | Value | Why |
|---|---|---|
| `--bind 0.0.0.0:8080` | Listen on all interfaces, port 8080 | Cloud Run expects port 8080 |
| `--workers 2` | 2 worker processes | Handle concurrent requests |
| `--timeout 60` | 60 second timeout | Kill slow requests to prevent hanging |
| `--log-file -` | Write logs to stdout | Cloud Logging captures stdout |
| `core.wsgi` | WSGI entry point | Located at `web/core/wsgi.py` |

---

## Build and test locally

Build the image:

```bash
docker build -t mycoolproject-app .
```

Test it locally (requires a local Postgres or mock DATABASE_URL):

```bash
docker run --rm \
  -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/mycoolproject_dev" \
  -e SECRET_KEY="local-test-key" \
  -e ALLOWED_HOSTS="localhost" \
  -p 8080:8080 \
  mycoolproject-app
```

Visit `http://localhost:8080` to verify it starts.

---

## The image naming

In `main.tf`, the Cloud Run service references the image:

```hcl
image = "${google_artifact_registry_repository.app.repository_url}/app:latest"
```

This resolves to:
```
southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:latest
```

GitHub Actions will push images with:
- `latest` tag — always points to the most recent build
- `<git-sha>` tag — unique per commit, for rollbacks

---

## Two-stage build (optional)

For smaller images, you can use a two-stage build:

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

This results in a smaller image because it excludes build tools. For simplicity, we use the single-stage version in this guide.

---

## Navigation



- [01 — Introduction: What We're Building](01_introduction.md)
- [02 — Terraform Overview](02_terraform_overview.md)
- [03 — Cloud Services Explained](03_cloud_services.md)
- [04 — PlanetScale Database Explained](04_planetscale.md)
- [05 — Project Setup & Terraform State](05_project_setup.md)
- [06 — GCP Project & APIs](06_gcp_project.md)
- [07 — Artifact Registry](07_artifact_registry.md)
- [08 — Secrets Management](09_secrets.md)
- [09 — Secret Manager](09_secrets.md)
- [10 — Cloud Storage](10_storage.md)
- [11 — Service Accounts & IAM](11_iam.md)
- [12 — Cloud Run](12_cloud_run.md)
- [13 — Cloud Tasks & Scheduler](13_tasks.md)
- 14 — Dockerfile (Current chapter)
- [15 — First Deploy](15_first_deploy.md)
- [16 — Custom Domain & SSL](16_domain_ssl.md)
- [17 — Workload Identity Federation](17_wif.md)
- [18 — GitHub Actions CI/CD](18_github_actions.md)
- [19 — Quick Reference](19_quick_reference.md)