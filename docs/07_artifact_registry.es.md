---
description: "Crea un registro privado de imágenes Docker en GCP usando Terraform."
image: assets/social-banner.png
---

# 07 — Artifact Registry

← [Anterior: 06 — Proyecto GCP y APIs](06_gcp_project.es.md)

Artifact Registry es donde se almacenan las imágenes Docker. Cuando GitHub Actions construye tu app, hace push de la imagen aquí. Cloud Run extrae de aquí al desplegar.

---

## ¿Qué es Artifact Registry?

Artifact Registry es el registro de contenedores privado de GCP — como Docker Hub, pero dentro de tu proyecto de GCP y privado. Las imágenes Docker se almacenan aquí, y solo Cloud Run (u otros servicios de GCP) pueden extraer de él.

¿Por qué privado? Porque la imagen contiene tu código. No quieres que sea públicamente accesible.

---

## Crear el registro con Terraform

Agrega a `infrastructure/main.tf`:

```hcl
# Artifact Registry repository for Docker images
resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = "app-repo"
  description   = "Docker images for MyCoolProject"
  format        = "DOCKER"

  # Cleanup on destroy (removes all images when you run terraform destroy)
  force_destroy = true
}

output "artifact_registry_url" {
  value       = google_artifact_registry_repository.app.repository_url
  description = "The URL of the Artifact Registry repository"
}
```

Ejecuta:

```bash
terraform plan   # Revisar
terraform apply  # Crear
```

### Qué crea esto

La URL del repositorio será:
```
southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo
```

Las imágenes empujadas aquí se nombrarán como:
```
southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:latest
southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:<git-sha>
```

---

## Configurar autenticación local de Docker

Para empujar imágenes desde tu máquina local, necesitas autenticar Docker en Artifact Registry. Esta es una configuración única por máquina:

```bash
gcloud auth configure-docker southamerica-east1-docker.pkg.dev
```

Esto actualiza `~/.docker/config.json` para usar tus credenciales de `gcloud` al empujar a este registro. GitHub Actions maneja esto automáticamente con su propia autenticación.

---

## Convenciones de nombres de imágenes

Usaremos dos etiquetas para cada imagen:

- `latest` — siempre apunta al build más reciente
- `<git-sha>` — una etiqueta única por commit (ej., `a3f9c12`) — habilita rollbacks precisos

El workflow de GitHub Actions:
1. Construye la imagen con ambas etiquetas
2. Empuja ambas etiquetas a Artifact Registry
3. Despliega usando la etiqueta `<git-sha>`

Así, si algo sale mal, puedes hacer rollback instantáneamente a la imagen anterior usando `git-sha`.

---

## Actualizar main.tf con todos los recursos hasta ahora

Después de completar los capítulos 05-07, tu `main.tf` debería contener:

```hcl
terraform {
  required_version = ">= 1.5.0"

  backend "gcs" {
    bucket = "mycoolproject-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required GCP APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "iam.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudscheduler.googleapis.com",
    "cloudtasks.googleapis.com",
  ])

  project = var.project_id
  service = each.value

  disable_dependent_services = false
  disable_on_destroy         = false
}

# Artifact Registry repository
resource "google_artifact_registry_repository" "app" {
  location      = var.region
  repository_id = "app-repo"
  description   = "Docker images for MyCoolProject"
  format        = "DOCKER"
  force_destroy = true
}

# Fetch project data
data "google_project" "project" {}

# Outputs
output "project_id" {
  value = var.project_id
}

output "project_number" {
  value = data.google_project.project.number
}

output "region" {
  value = var.region
}

output "artifact_registry_url" {
  value = google_artifact_registry_repository.app.repository_url
}
```

---

## Navegación



- [01 — Introducción: Qué vamos a construir](01_introduction.es.md)
- [02 — Visión general de Terraform](02_terraform_overview.es.md)
- [03 — Servicios en la nube explicados](03_cloud_services.es.md)
- [04 — Base de datos PlanetScale explicada](04_planetscale.es.md)
- [05 — Configuración del proyecto y estado de Terraform](05_project_setup.es.md)
- [06 — Proyecto GCP y APIs](06_gcp_project.es.md)
- 07 — Artifact Registry (Capítulo actual)
- [08 — Gestión de Secretos](09_secrets.es.md)
- [09 — Cloud Storage](10_storage.es.md)
- [10 — Service Accounts e IAM](11_iam.es.md)
- [11 — Cloud Run](12_cloud_run.es.md)
- [12 — Trabajos en segundo plano y Scheduler](13_tasks.es.md)
- [13 — Dockerfile](14_dockerfile.es.md)
- [14 — Primer Despliegue](15_first_deploy.es.md)
- [15 — Dominio personalizado y SSL](16_domain_ssl.es.md)
- [16 — Workload Identity Federation](17_wif.es.md)
- [17 — GitHub Actions CI/CD](18_github_actions.es.md)
- [18 — Referencia Rápida](19_quick_reference.es.md)
