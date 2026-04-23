---
description: "Crea service accounts y configura permisos IAM para Cloud Run y otros servicios de GCP."
image: assets/social-banner.png
---

# 10 — Service Accounts e IAM

← [Anterior: 09 — Cloud Storage](10_storage.es.md)

Las service accounts son identidades que Cloud Run y otros servicios usan para acceder a otros recursos de GCP. Este capítulo crea la service account y le otorga solo los permisos que necesita.

---

## Principio de mínimo privilegio

Seguimos el principio de mínimo privilegio: dar a cada identidad solo los permisos que necesita, nada más.

Nuestro servicio web de Cloud Run necesita:
- **Secret Manager** — leer secretos (DATABASE_URL, SECRET_KEY, etc.)
- **Cloud Storage** — leer/escribir buckets estáticos y de medios

NO necesita:
- Cloud SQL Admin (no estamos usando Cloud SQL)
- Compute Admin (no estamos ejecutando VMs)
- IAM completo (demasiado amplio)

---

## Crear service account con Terraform

Agrega a `infrastructure/main.tf`:

```hcl
# Service account for Cloud Run
resource "google_service_account" "run" {
  account_id   = "mycoolproject-run"
  display_name = "MyCoolProject Cloud Run Service Account"
}

# Grant permissions to read secrets
resource "google_project_iam_member" "run_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.run.email}"
}

# Grant permissions to manage storage buckets
resource "google_project_iam_member" "run_storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.run.email}"
}

# Grant permissions to manage Cloud Tasks
resource "google_project_iam_member" "run_cloudtasks_admin" {
  project = var.project_id
  role    = "roles/cloudtasks.admin"
  member  = "serviceAccount:${google_service_account.run.email}"
}
```

Ejecuta `terraform apply` para crear la service account y los permisos.

---

## Formato del email de service account

El email de la service account será:
```
mycoolproject-run@mycoolproject-prod.iam.gserviceaccount.com
```

Este formato se usa en todo Terraform y comandos `gcloud` para referenciar la identidad.

---

## Service account para el worker de Cloud Tasks

El worker de Cloud Tasks (Cloud Run Job) necesita sus propios permisos para ejecutar comandos de gestión de Django y acceder a secretos:

```hcl
# Service account for Cloud Tasks worker (background jobs)
resource "google_service_account" "worker" {
  account_id   = "mycoolproject-worker"
  display_name = "MyCoolProject Worker Service Account"
}

# Grant same permissions as web service account
resource "google_project_iam_member" "worker_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "worker_storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.worker.email}"
}

resource "google_project_iam_member" "worker_cloudtasks_admin" {
  project = var.project_id
  role    = "roles/cloudtasks.admin"
  member  = "serviceAccount:${google_service_account.worker.email}"
}
```

---

## Resumen de roles IAM

| Service Account | Rol | Por qué |
|---|---|---|
| `mycoolproject-run` | `secretmanager.secretAccessor` | Leer secretos (DB, clave secreta, etc.) |
| `mycoolproject-run` | `storage.objectAdmin` | Leer/escribir archivos estáticos y de medios |
| `mycoolproject-run` | `cloudtasks.admin` | Encolar tareas desde el servicio web |
| `mycoolproject-worker` | `secretmanager.secretAccessor` | Leer secretos para trabajos en segundo plano |
| `mycoolproject-worker` | `storage.objectAdmin` | Escribir archivos procesados si es necesario |
| `mycoolproject-worker` | `cloudtasks.admin` | Procesar tareas de la cola |

---

## Outputs para emails de service accounts

Agrega a `main.tf`:

```hcl
output "run_service_account_email" {
  value = google_service_account.run.email
}

output "worker_service_account_email" {
  value = google_service_account.worker.email
}
```

---

## Verificar las service accounts

```bash
gcloud iam service-accounts list --project=mycoolproject-prod
```

Deberías ver tanto `mycoolproject-run` como `mycoolproject-worker`.

---

## Qué hemos construido hasta ahora

Después de los capítulos 05-10, Terraform ha creado:
- Proyecto GCP con APIs habilitadas
- Repositorio de Artifact Registry
- Secretos de Secret Manager (estructura, no valores)
- Buckets de Cloud Storage (estáticos + medios)
- Service accounts con permisos IAM

Próximo: Servicio de Cloud Run (el servidor web real).

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
- 10 — Service Accounts e IAM (Capítulo actual)
- [11 — Cloud Run](12_cloud_run.es.md)
- [12 — Trabajos en segundo plano y Scheduler](13_tasks.es.md)
- [13 — Dockerfile](14_dockerfile.es.md)
- [14 — Primer Despliegue](15_first_deploy.es.md)
- [15 — Dominio personalizado y SSL](16_domain_ssl.es.md)
- [16 — Workload Identity Federation](17_wif.es.md)
- [17 — GitHub Actions CI/CD](18_github_actions.es.md)
- [18 — Referencia Rápida](19_quick_reference.es.md)
