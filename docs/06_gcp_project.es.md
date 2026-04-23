---
description: "Crea un proyecto GCP, habilita las APIs necesarias y configura la CLI de gcloud."
image: assets/social-banner.png
---

# 06 — Proyecto GCP y APIs

← [Anterior: 05 — Configuración del proyecto y estado de Terraform](05_project_setup.es.md)

Antes de que Terraform pueda crear recursos, necesitamos un proyecto de GCP y debemos habilitar las APIs que Terraform gestionará.

---

## Crear un proyecto de GCP

Si aún no tienes un proyecto de GCP, crea uno:

```bash
# Crear un nuevo proyecto
gcloud projects create mycoolproject-prod --name="My Cool Project"

# Establecerlo como tu proyecto activo
gcloud config set project mycoolproject-prod
```

Si ya tienes un proyecto, salta a establecer el proyecto activo:

```bash
gcloud config set project mycoolproject-prod
```

Obtén tu ID de proyecto (lo necesitarás para Terraform):

```bash
gcloud projects describe mycoolproject-prod --format='value(projectId)'
```

---

## Habilitar APIs de GCP

Terraform gestiona estos servicios de GCP, así que necesitamos habilitar sus APIs:

```bash
# Habilitar APIs necesarias para esta guía
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  cloudscheduler.googleapis.com \
  tasks.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com
```

Estas APIs alimentan Cloud Run, Cloud Storage, Secret Manager y más.

---

## ID de Proyecto vs Número de Proyecto

- **Project ID** — tu identificador único (ej., `mycoolproject-prod`)
- **Project Number** — un identificador numérico (ej., `123456789012`)

Terraform usa ambos:
- `project` en la configuración del provider = ID del proyecto
- Algunos recursos necesitan el número de proyecto para enlaces de IAM

Obtén tu número de proyecto:

```bash
gcloud projects describe mycoolproject-prod --format='value(projectNumber)'
```

Agrega ambos a `infrastructure/terraform.tfvars`:

```hcl
project_id      = "mycoolproject-prod"
project_number  = "123456789012"
region          = "southamerica-east1"
```

---

## Terraform: Habilitar APIs vía recurso

Alternativamente, puedes dejar que Terraform habilite las APIs automáticamente usando el recurso `google-project-service-enforcement`. Agrega a `main.tf`:

```hcl
# Habilitar APIs requeridas
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudscheduler.googleapis.com",
    "tasks.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
  ])

  project = var.project_id
  service = each.value

  disable_dependent_services = false
  disable_on_destroy         = false
}
```

Este enfoque hace que la habilitación de APIs sea parte de tu estado de Terraform — útil para reproducibilidad.

---

## Navegación



- [01 — Introducción: Qué vamos a construir](01_introduction.es.md)
- [02 — Visión general de Terraform](02_terraform_overview.es.md)
- [03 — Servicios en la nube explicados](03_cloud_services.es.md)
- [04 — Base de datos PlanetScale explicada](04_planetscale.es.md)
- [05 — Configuración del proyecto y estado de Terraform](05_project_setup.es.md)
- 06 — Proyecto GCP y APIs (Capítulo actual)
- [07 — Artifact Registry](07_artifact_registry.es.md)
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
