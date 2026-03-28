---
description: "Step 6: Write a production-ready Dockerfile optimized for running Django apps on Cloud Run using uv."
---
# 06 — Dockerfile

← [Previous: 05 — Cloud Storage (Media & Static Files)](05_cloud_storage.md)

## What is a Dockerfile?

A Dockerfile is a recipe for building a Docker image. It starts from a base image (e.g. a minimal Linux OS with Python), copies your code in, installs dependencies, and defines the command to start the application. The result is a single portable artifact that can run identically on any machine or cloud platform.

## Where does it go?

The Dockerfile lives at the **repo root**.

---

## Dockerfile

Create `Dockerfile` at project root directory:

```dockerfile
# ── Base image ────────────────────────────────────────────────────────────────
# python:3.12-slim is a minimal Debian image with Python 3.12.
# "slim" means no build tools, compilers, or docs — smaller image size.
FROM python:3.12-slim

# ── Install uv ───────────────────────────────────────────────────────────────
# uv is the package manager this project uses instead of pip.
# We copy the uv binary from its official Docker image rather than installing it.
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

# ── Environment ───────────────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=core.settings.prod \
    PORT=8080
# PYTHONDONTWRITEBYTECODE: don't write .pyc files (unnecessary in containers)
# PYTHONUNBUFFERED: flush stdout/stderr immediately (so logs appear in real time)
# DJANGO_SETTINGS_MODULE: tells Django to use prod.py settings
# PORT: Cloud Run injects this; Gunicorn reads it

EXPOSE 8080

# ── Start command ─────────────────────────────────────────────────────────────
# Gunicorn is a production-grade WSGI server. It runs Django's wsgi.py application.
# Gunicorn must be in your uv.lock file
# Django's built-in dev server (manage.py runserver) must NEVER be used in prod.
CMD ["uv", "run", "gunicorn", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--timeout", "60", \
     "--log-file", "-", \
     "core.wsgi"]
```

Gunicorn options:
- `--bind 0.0.0.0:8080` — listen on all interfaces, port 8080 (Cloud Run's expected port)
- `--workers 2` — 2 worker processes handle requests concurrently
- `--timeout 60` — kill workers that take longer than 60 s (prevents hanging requests)
- `--log-file -` — write logs to stdout so Cloud Logging captures them
- `core.wsgi` — the WSGI entry point at `web/core/wsgi.py`

---

## .dockerignore

Create `.dockerignore` at the repo root. Docker excludes these from the build context — keeping the image small and preventing secrets from leaking in:

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

---

## Build and test locally

Run from the repo root:

```bash
# Builds the Docker image from the Dockerfile at the repo root.
# -t mycoolproject-app gives the image a local name for testing.
# Result: image listed in `docker images` as mycoolproject-app:latest
docker build -t mycoolproject-app .
```

Test it locally (requires a running PostgreSQL):

> **Platform note:** `host.docker.internal` is specific to **Docker Desktop (Windows/Mac)**. On **Linux**, replace it with your host machine's IP address (e.g. `172.17.0.1`) or use `localhost` if PostgreSQL is listening on the Docker bridge. Check with `docker inspect bridge` if needed.

```bash
# Runs the built image locally to verify it starts correctly before pushing to GCP.
# --rm removes the container when it stops (keeps Docker clean).
# host.docker.internal resolves to your host machine's IP from inside the container.
# -p 8080:8080 maps container port 8080 to localhost:8080.
# Result: visit http://localhost:8080 — should see the MyCoolProject homepage.
docker run --rm \
  -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/mycoolproject_dev" \
  -e SECRET_KEY="local-test-key" \
  -e ALLOWED_HOSTS="localhost" \
  -p 8080:8080 \
  mycoolproject-app
```

Then visit `http://localhost:8080`. If it starts, the image is correct.

---

## How the image flows to production

```
docker build → image on your machine
    └── docker push → Artifact Registry (chapter 02)
                          └── Cloud Run pulls → runs as container (chapter 07)
```

After the first manual deploy, GitHub Actions handles build and push automatically on every commit. More details in [next chapter](07_first_deploy.md).

---

## 📖 Navigation

- [01 — GCP Project Setup](01_gcp_setup.md)
- [02 — Artifact Registry](02_artifact_registry.md)
- [03 — Cloud SQL (PostgreSQL Database)](03_cloud_sql.md)
- [04 — Secret Manager](04_secret_manager.md)
- [05 — Cloud Storage (Media & Static Files)](05_cloud_storage.md)
- **06 — Dockerfile** (current chapter)
- [07 — First Deploy](07_first_deploy.md)
- [08 — Custom Domain & SSL](08_domain_ssl.md)
- [09 — Workload Identity Federation (Keyless GitHub Actions Auth)](09_workload_identity.md)
- [10 — GitHub Actions CI/CD Pipeline](10_github_actions.md)
- [11 — Quick Reference](11_quick_reference.md)
