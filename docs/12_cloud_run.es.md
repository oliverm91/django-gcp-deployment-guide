---
description: "Crea el servicio Cloud Run usando Terraform y comprende cómo configurarlo para Django."
image: assets/social-banner.png
---

# 11 — Cloud Run

← [Anterior: 10 — Service Accounts e IAM](11_iam.es.md)

Cloud Run es donde se ejecuta tu aplicación Django. Este capítulo crea el servicio Cloud Run con Terraform y explica todas las opciones de configuración.

---

## Conceptos básicos de Cloud Run

Cloud Run toma una imagen Docker y la ejecuta como un servicio. Este:
- Inicia cuando llegan solicitudes (o se mantiene en 0 instancias si `--min-instances=0`)
- Escala automáticamente bajo carga
- Escala a cero cuando está inactivo (sin costo)
- Maneja HTTPS automáticamente

---

## Crear el servicio Cloud Run

Agrega a `infrastructure/main.tf`:

```hcl
# Cloud Run service for the web app
resource "google_cloud_run_service" "web" {
  name     = "mycoolproject"
  location = var.region

  template {
    spec {
      # Which service account this container runs as
      service_account_name = google_service_account.run.email

      # Container configuration
      containers {
        image = "${google_artifact_registry_repository.app.repository_url}/app:latest"
        ports {
          container_port = 8080
        }
        # Environment variables from secrets
        env {
          name = "DJANGO_SETTINGS_MODULE"
          value = "core.settings.prod"
        }
        env {
          name = "PORT"
          value = "8080"
        }
        env {
          name = "PYTHONUNBUFFERED"
          value = "1"
        }
        # Secret values injected as env vars
        env {
          name = "DATABASE_URL"
          value_from {
            secret_key_ref {
              name = "DATABASE_URL"
              secret_key = "latest"
            }
          }
        }
        env {
          name = "SECRET_KEY"
          value_from {
            secret_key_ref {
              name = "DJANGO_SECRET_KEY"
              secret_key = "latest"
            }
          }
        }
        env {
          name = "ALLOWED_HOSTS"
          value = "mycoolproject.com,www.mycoolproject.com"
        }
      }

      # Scaling configuration
      min_scale = 0
      max_scale = 5

      # Resource limits
      resources {
        limits {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    # Timeout (max request duration)
    timeout = "60s"
  }

  # Allow public access (no authentication)
  traffic {
    revision_suffix = "initial"
    percent          = 100
  }
}

# Make Cloud Run service publicly accessible
resource "google_cloud_run_service_iam_member" "web_public" {
  location = google_cloud_run_service.web.location
  service  = google_cloud_run_service.web.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "web_service_url" {
  value = google_cloud_run_service.web.status[0].url
}
```

Ejecuta `terraform apply` para crear el servicio.

---

## Configuración clave explicada

### `service_account_name`

El contenedor se ejecuta como esta service account, que tiene permisos para:
- Leer secretos
- Acceder a Cloud Storage
- Encolar Cloud Tasks

### `image`

Apunta a la imagen en Artifact Registry. Usamos `app:latest` por ahora, pero GitHub Actions desplegará con una etiqueta `<git-sha>` para rollbacks.

### `ports`

Cloud Run espera el puerto 8080 por defecto. Lo establecemos explícitamente.

### `env` desde secretos

En lugar de `--set-secrets` en `gcloud`, definimos vars de entorno desde secretos directamente en Terraform.

### `min_scale = 0` (escala a cero)

Cuando no hay tráfico, Cloud Run escala a cero instancias. Esto significa sin costo. La primera solicitud después de inactividad toma 1-2 segundos en iniciar (cold start).

### `max_scale = 5`

Límite duro en instancias. Previene escalada descontrolada por picos de tráfico.

### `timeout = "60s"`

Duración máxima para una sola solicitud. Si una solicitud toma más, Cloud Run la mata.

### `resources`

Límites de CPU y memoria. Django con Gunicorn típicamente necesita 512Mi y 1 CPU.

---

## Actualizar imagen después de que GitHub Actions construye

Después de que GitHub Actions construye y hace push de la imagen con una etiqueta `<git-sha>`, actualizamos Cloud Run:

```bash
gcloud run services update mycoolproject \
  --image=southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:<git-sha> \
  --region=southamerica-east1
```

---

## Endpoint de health check

Cloud Run necesita un health check para saber si el contenedor está ejecutándose. Django debería tener un endpoint `/health/` que retorne `{"status": "ok"}`.

En `web/core/urls.py`:

```python
from django.http import JsonResponse

urlpatterns = [
    # ... other routes ...
    path("health/", lambda request: JsonResponse({"status": "ok"})),
]
```

---

## Actualizar en despliegue

Cuando haces push de código, GitHub Actions:
1. Construye imagen Docker
2. Hace push a Artifact Registry con etiqueta `<git-sha>`
3. Actualiza Cloud Run para usar la nueva imagen

---

## Verificar el servicio

```bash
# Obtener la URL del servicio
gcloud run services describe mycoolproject --region=southamerica-east1 --format="value(status.url)"

# Probarlo
curl <url>/health/
```

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
- 11 — Cloud Run (Capítulo actual)
- [12 — Trabajos en segundo plano y Scheduler](13_tasks.es.md)
- [13 — Dockerfile](14_dockerfile.es.md)
- [14 — Primer Despliegue](15_first_deploy.es.md)
- [15 — Dominio personalizado y SSL](16_domain_ssl.es.md)
- [16 — Workload Identity Federation](17_wif.es.md)
- [17 — GitHub Actions CI/CD](18_github_actions.es.md)
- [18 — Referencia Rápida](19_quick_reference.es.md)
