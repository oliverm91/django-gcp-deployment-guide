---
description: "Escribe un Dockerfile listo para producción, optimizado para ejecutar apps Django en Cloud Run usando uv."
image: assets/social-banner.png

---
# 06 — Dockerfile

← [Anterior: 05 — Cloud Storage (Archivos media y static)](05_cloud_storage.md)

## ¿Qué es un Dockerfile?

Un Dockerfile es una receta para construir una imagen Docker. Parte de una imagen base (por ejemplo, un sistema Linux mínimo con Python), copia tu código, instala las dependencias y define el comando para iniciar la aplicación. El resultado es un artefacto único y portable que puede ejecutarse de manera idéntica en cualquier máquina o plataforma en la nube.

## ¿Dónde va?

El Dockerfile vive en la **raíz del repositorio**.

---

## Dockerfile

Crea `Dockerfile` en el directorio raíz del proyecto:

```dockerfile
# ── Imagen base ────────────────────────────────────────────────────────────────
# python:3.12-slim es una imagen Debian mínima con Python 3.12.
# "slim" significa sin herramientas de compilación, compiladores ni documentación — imagen más pequeña.
FROM python:3.12-slim

# ── Instalar uv ───────────────────────────────────────────────────────────────
# uv es el gestor de paquetes que usa este proyecto en lugar de pip.
# Copiamos el binario de uv desde su imagen Docker oficial en lugar de instalarlo.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# ── Directorio de trabajo ─────────────────────────────────────────────────────
# Todos los comandos siguientes se ejecutan desde /app dentro del contenedor.
WORKDIR /app

# ── Instalar dependencias Python ───────────────────────────────────────────────
# Copia solo los archivos de dependencias primero (no el código fuente completo).
# Docker guarda en caché cada capa — si pyproject.toml y uv.lock no cambiaron,
# esta capa se reutiliza en el próximo build, haciendo las compilaciones mucho más rápidas.
COPY web/pyproject.toml web/uv.lock ./
RUN uv sync --frozen --no-dev
# --frozen: falla si uv.lock está desactualizado (asegura builds reproducibles)
# --no-dev: omite dependencias de solo desarrollo (django_extensions, herramientas de testing, etc.)

# ── Copiar código fuente de la aplicación ───────────────────────────────────────────────────────────
# Copiado después de instalar dependencias para que los cambios de código no invaliden la caché de dependencias.
COPY web/ .

# ── Variables de entorno ───────────────────────────────────────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=core.settings.prod \
    PORT=8080
# PYTHONDONTWRITEBYTECODE: no escribir archivos .pyc (innecesarios en contenedores)
# PYTHONUNBUFFERED: vaciar stdout/stderr inmediatamente (para que los logs aparezcan en tiempo real)
# DJANGO_SETTINGS_MODULE: le indica a Django que use la configuración de prod.py
# PORT: Cloud Run inyecta esto; Gunicorn lo lee

EXPOSE 8080

# ── Comando de inicio ─────────────────────────────────────────────────────────
# Gunicorn es un servidor WSGI de grado de producción. Ejecuta la aplicación wsgi.py de Django.
# Gunicorn debe estar en tu archivo uv.lock
# El servidor de desarrollo incorporado de Django (manage.py runserver) NUNCA debe usarse en producción.
CMD ["uv", "run", "gunicorn", \
     "--bind", "0.0.0.0:8080", \
     "--workers", "2", \
     "--timeout", "60", \
     "--log-file", "-", \
     "core.wsgi"]
```

Opciones de Gunicorn:

- `--bind 0.0.0.0:8080` — escucha en todas las interfaces, puerto 8080 (el puerto esperado por Cloud Run)
- `--workers 2` — 2 procesos worker manejan solicitudes de forma concurrente
- `--timeout 60` — termina workers que tardan más de 60 s (previene solicitudes colgadas)
- `--log-file -` — escribe logs en stdout para que Cloud Logging los capture
- `core.wsgi` — el punto de entrada WSGI en `web/core/wsgi.py`

---

## .dockerignore

Crea `.dockerignore` en la raíz del repositorio. Docker excluye estos archivos del contexto de build — manteniendo la imagen pequeña y evitando que los secrets se filtren:

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

## Construir y probar localmente

Ejecuta desde la raíz del repositorio:

```bash
# Construye la imagen Docker desde el Dockerfile en la raíz del repositorio.
# -t mycoolproject-app le da a la imagen un nombre local para pruebas.
# Resultado: imagen listada en `docker images` como mycoolproject-app:latest
docker build -t mycoolproject-app .
```

Pruébala localmente (requiere PostgreSQL en ejecución):

> **Nota de plataforma:** `host.docker.internal` es específico de **Docker Desktop (Windows/Mac)**. En **Linux**, reemplázalo con la IP de tu máquina anfitriona (por ejemplo, `172.17.0.1`) o usa `localhost` si PostgreSQL está escuchando en el puente Docker. Verifica con `docker inspect bridge` si es necesario.

```bash
# Ejecuta la imagen construida localmente para verificar que arranca correctamente antes de subirla a GCP.
# --rm elimina el contenedor cuando se detiene (mantiene Docker limpio).
# host.docker.internal se resuelve a la IP de tu máquina anfitriona desde dentro del contenedor.
# -p 8080:8080 mapea el puerto 8080 del contenedor al puerto 8080 de localhost.
# Resultado: visita http://localhost:8080 — debería mostrar la página de inicio de MyCoolProject.
docker run --rm \
  -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/mycoolproject_dev" \
  -e SECRET_KEY="local-test-key" \
  -e ALLOWED_HOSTS="localhost" \
  -p 8080:8080 \
  mycoolproject-app
```

Luego visita `http://localhost:8080`. Si arranca, la imagen es correcta.

---

## Cómo fluye la imagen a producción

```
docker build → imagen en tu máquina
    └── docker push → Artifact Registry (capítulo 02)
                          └── Cloud Run descarga → ejecuta como contenedor (capítulo 07)
```

Después del primer despliegue manual, GitHub Actions maneja el build y push automáticamente en cada commit. Más detalles en el [capítulo siguiente](07_first_deploy.md).

---

## 📖 Navegación

- [01 — Configuración del Proyecto GCP](01_gcp_setup.md)
- [02 — Artifact Registry](02_artifact_registry.md)
- [03 — Cloud SQL (Base de Datos PostgreSQL)](03_cloud_sql.md)
- [04 — Secret Manager](04_secret_manager.md)
- [05 — Cloud Storage (Archivos media y static)](05_cloud_storage.md)
- **06 — Dockerfile** (capítulo actual)
- [07 — Primer Despliegue](07_first_deploy.md)
- [08 — Dominio Personalizado y SSL](08_domain_ssl.md)
- [09 — Workload Identity Federation (Autenticación sin claves en GitHub Actions)](09_workload_identity.md)
- [10 — Pipeline CI/CD con GitHub Actions](10_github_actions.md)
- [11 — Referencia Rápida](11_quick_reference.md)
