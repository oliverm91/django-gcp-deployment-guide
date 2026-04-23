---
description: "Create a private Docker image registry in GCP using Terraform."
image: assets/social-banner.png
---

# 07 — Artifact Registry

← [Previous: 06 — GCP Project & APIs](06_gcp_project.md)

Artifact Registry is where Docker images are stored. When GitHub Actions builds your app, it pushes the image here. Cloud Run pulls from here when deploying.

---

## What is Artifact Registry?

Artifact Registry is GCP's private container registry — like Docker Hub, but inside your GCP project and private. Docker images are stored here, and only Cloud Run (or other GCP services) can pull from it.

Why private? Because the image contains your code. You don't want it publicly accessible.

---

## Create the registry with Terraform

Add to `infrastructure/main.tf`:

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

Run:

```bash
terraform plan   # Review
terraform apply  # Create
```

### What this creates

The repository URL will be:
```
southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo
```

Images pushed here will be named like:
```
southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:latest
southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:<git-sha>
```

---

## Configure local Docker authentication

To push images from your local machine, you need to authenticate Docker to Artifact Registry. This is a one-time setup per machine:

```bash
gcloud auth configure-docker southamerica-east1-docker.pkg.dev
```

This updates `~/.docker/config.json` to use your `gcloud` credentials when pushing to this registry. GitHub Actions handles this automatically with its own authentication.

---

## Image naming convention

We'll use two tags for each image:

- `latest` — always points to the most recent build
- `<git-sha>` — a unique tag per commit (e.g., `a3f9c12`) — enables precise rollbacks

GitHub Actions workflow will:
1. Build the image with both tags
2. Push both tags to Artifact Registry
3. Deploy using the `<git-sha>` tag

This way, if something goes wrong, you can instantly roll back to the previous image using `git-sha`.

---

## Update main.tf with all resources so far

After completing chapters 05-07, your `main.tf` should contain:

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
    "servicenetworking.googleapis.com",
    "vpcaccess.googleapis.com",
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

## Navigation



- [01 — Introduction: What We're Building](01_introduction.md)
- [02 — Terraform Overview](02_terraform_overview.md)
- [03 — Cloud Services Explained](03_cloud_services.md)
- [04 — PlanetScale Database Explained](04_planetscale.md)
- [05 — Project Setup & Terraform State](05_project_setup.md)
- [06 — GCP Project & APIs](06_gcp_project.md)
- 07 — Artifact Registry (Current chapter)
- [08 — Secrets Management](09_secrets.md)
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