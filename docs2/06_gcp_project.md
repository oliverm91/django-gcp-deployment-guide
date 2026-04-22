---
description: "Create a GCP project, enable necessary APIs, and configure the gcloud CLI."
image: assets/social-banner.png
---

# 06 — GCP Project & APIs

← [Previous: 05 — Project Setup & Terraform State](05_project_setup.md)

Before Terraform can create resources, we need a GCP project and must enable the APIs that Terraform will manage.

---

## Create a GCP project

If you don't have a GCP project yet, create one:

```bash
# Create a new project
gcloud projects create mycoolproject-prod --name="My Cool Project"

# Set it as your active project
gcloud config set project mycoolproject-prod
```

If you already have a project, skip to setting the active project:

```bash
gcloud config set project mycoolproject-prod
```

Get your project ID (you'll need it for Terraform):

```bash
gcloud projects describe mycoolproject-prod --format='value(projectId)'
```

---

## Enable GCP APIs

Terraform manages these GCP services, so we need to enable their APIs:

```bash
# Enable APIs needed for this guide
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  cloudscheduler.googleapis.com \
  tasks.googleapis.com \
  storage.googleapis.com \
  secretmanager.googleapis.com \
  vpcaccess.googleapis.com \
  servicenetworking.googleapis.com \
  compute.googleapis.com
```

These APIs power Cloud Run, Cloud Storage, Secret Manager, Serverless VPC, and more.

---

## Project ID vs Project Number

- **Project ID** — your unique identifier (e.g., `mycoolproject-prod`)
- **Project Number** — a numeric identifier (e.g., `123456789012`)

Terraform uses both:
- `project` in provider config = project ID
- Some resources need project number for IAM bindings

Get your project number:

```bash
gcloud projects describe mycoolproject-prod --format='value(projectNumber)'
```

Add both to `infrastructure/terraform.tfvars`:

```hcl
project_id      = "mycoolproject-prod"
project_number  = "123456789012"
region          = "southamerica-east1"
```

---

## Terraform: Enable APIs via resource

Alternatively, you can let Terraform enable APIs automatically using the `google-project-service-enforcement` resource. Add to `main.tf`:

```hcl
# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com",
    "cloudscheduler.googleapis.com",
    "tasks.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "vpcaccess.googleapis.com",
    "servicenetworking.googleapis.com",
    "compute.googleapis.com",
  ])

  project = var.project_id
  service = each.value

  disable_dependent_services = false
  disable_on_destroy         = false
}
```

This approach makes API enablement part of your Terraform state — useful for reproducibility.

---

## Navigation



- [01 — Introduction: What We're Building](01_introduction.md)
- [02 — Terraform Overview](02_terraform_overview.md)
- [03 — Cloud Services Explained](03_cloud_services.md)
- [04 — PlanetScale Database Explained](04_planetscale.md)
- [05 — Project Setup & Terraform State](05_project_setup.md)
- 06 — GCP Project & APIs (Current chapter)
- [07 — Artifact Registry](07_artifact_registry.md)
- [08 — PlanetScale Database](08_planetscale_db.md)
- [09 — Secret Manager](09_secrets.md)
- [10 — Cloud Storage](10_storage.md)
- [11 — Service Accounts & IAM](11_iam.md)
- [12 — Cloud Run](12_cloud_run.md)
- [13 — Cloud Tasks & Scheduler](13_tasks.md)
- [14 — Dockerfile](14_dockerfile.md)
- [15 — First Deploy](15_first_deploy.md)
- [16 — Custom Domain & SSL](16_domain_ssl.md)
- [17 — Workload Identity Federation](17_wif.md)
- [18 — GitHub Actions CI/CD](18_github_actions.md)
- [19 — Quick Reference](19_quick_reference.md)