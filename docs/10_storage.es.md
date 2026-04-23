---
description: "Crea buckets de Cloud Storage para archivos estáticos y medios subidos usando Terraform."
image: assets/social-banner.png
---

# 09 — Cloud Storage

← [Anterior: 08 — Gestión de Secretos](09_secrets.es.md)

Cloud Storage (GCS) almacena archivos estáticos y medios subidos por usuarios. Crearemos dos buckets con Terraform: uno para archivos estáticos (CSS, JS) y uno para medios (subidas de usuarios).

---

## ¿Por qué dos buckets?

| Bucket | Contenido | Quién escribe | Quién lee |
|---|---|---|---|
| `static` | CSS, JS, íconos — de `collectstatic` | Django (en tiempo de despliegue) | Navegadores directamente |
| `media` | Imágenes subidas por usuarios, avatares | Django (en tiempo de ejecución) | Navegadores directamente |

Ambos son públicamente legibles para que los navegadores puedan obtener archivos directamente sin pasar por Django.

---

## Crear los buckets con Terraform

Agrega a `infrastructure/main.tf`:

```hcl
# Cloud Storage buckets
resource "google_storage_bucket" "static" {
  name          = "${var.project_id}-static"
  location      = var.region
  force_destroy = true

  # Uniform bucket-level access (simpler, recommended)
  uniform_bucket_level_access = true

  # Public access prevention (keep off so we can make public)
  public_access_prevention = "inherited"
}

resource "google_storage_bucket" "media" {
  name          = "${var.project_id}-media"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true
  public_access_prevention    = "inherited"
}

# Make static bucket publicly readable
resource "google_storage_bucket_iam_member" "static_public" {
  bucket = google_storage_bucket.static.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# Make media bucket publicly readable
resource "google_storage_bucket_iam_member" "media_public" {
  bucket = google_storage_bucket.media.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# Allow Cloud Run service account to write to both buckets
resource "google_storage_bucket_iam_member" "run_static_admin" {
  bucket = google_storage_bucket.static.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.run.email}"
}

resource "google_storage_bucket_iam_member" "run_media_admin" {
  bucket = google_storage_bucket.media.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.run.email}"
}

output "static_bucket" {
  value = google_storage_bucket.static.name
}

output "media_bucket" {
  value = google_storage_bucket.media.name
}
```

Ejecuta `terraform apply` para crear ambos buckets.

---

## Qué se crea

| Bucket nombre | URL | Propósito |
|---|---|---|
| `mycoolproject-prod-static` | `https://storage.googleapis.com/mycoolproject-prod-static/` | CSS, JS, fuentes |
| `mycoolproject-prod-media` | `https://storage.googleapis.com/mycoolproject-prod-media/` | Subidas de usuarios |

---

## Configuración de Django

En `web/core/settings/prod.py`:

```python
STORAGES = {
    # Default storage: user uploads go here
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": "${var.project_id}-media",
        },
    },
    # Static files: collectstatic uploads here
    "staticfiles": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": "${var.project_id}-static",
            "default_acl": None,  # Removes public ACL, relies on bucket policy
            "object_parameters": {
                "cache_control": "public, max-age=31536000",
            },
        },
    },
}

GS_PROJECT_ID = var.project_id
STATIC_URL = f"https://storage.googleapis.com/${var.project_id}-static/"
MEDIA_URL = f"https://storage.googleapis.com/${var.project_id}-media/"
```

---

## Collectstatic: subir archivos estáticos

Antes de desplegar, ejecuta `collectstatic` para subir CSS, JS y fuentes a GCS:

```bash
cd web
DJANGO_SETTINGS_MODULE=core.settings.prod uv run manage.py collectstatic --noinput
```

Esto sube todos los archivos estáticos al bucket estático. El backend de GCS de Django maneja esto automáticamente vía la librería `storages`.

---

## No hay archivos media para colectar

Los archivos media (subidas de usuarios) se suben en tiempo de ejecución cuando los usuarios envían formularios. No hay equivalente de `collectstatic` — Django escribe directamente a GCS vía el backend de `storages`.

---

## Verificar que los buckets existen

```bash
gsutil ls
```

Deberías ver:
```
gs://mycoolproject-prod-static/
gs://mycoolproject-prod-media/
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
- 09 — Cloud Storage (Capítulo actual)
- [10 — Service Accounts e IAM](11_iam.es.md)
- [11 — Cloud Run](12_cloud_run.es.md)
- [12 — Trabajos en segundo plano y Scheduler](13_tasks.es.md)
- [13 — Dockerfile](14_dockerfile.es.md)
- [14 — Primer Despliegue](15_first_deploy.es.md)
- [15 — Dominio personalizado y SSL](16_domain_ssl.es.md)
- [16 — Workload Identity Federation](17_wif.es.md)
- [17 — GitHub Actions CI/CD](18_github_actions.es.md)
- [18 — Referencia Rápida](19_quick_reference.es.md)
