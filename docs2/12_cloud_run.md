---
description: "Create the Cloud Run service using Terraform and understand how to configure it for Django."
image: assets/social-banner.png
---

# 12 — Cloud Run

← [Previous: 11 — Service Accounts & IAM](11_iam.md)

Cloud Run is where your Django app runs. This chapter creates the Cloud Run service with Terraform and explains all the configuration options.

---

## Cloud Run basics

Cloud Run takes a Docker image and runs it as a service. It:
- Starts when requests come in (or stays at 0 instances if `--min-instances=0`)
- Scales up automatically under load
- Scales to zero when idle (no cost)
- Handles HTTPS automatically

---

## Create the Cloud Run service

Add to `infrastructure/main.tf`:

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
        # The secret name must match what's in Secret Manager
        # The env var name is what Django reads
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

    # VPC connector (optional - for PlanetScale connection)
    # vpc_access {
    #   connector = google_vpc_access_connector.planetscale.name
    #   egress   = "ALL_TRAFFIC"
    # }

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

Run `terraform apply` to create the service.

---

## Key configuration explained

### `service_account_name`

The container runs as this service account, which has permissions to:
- Read secrets
- Access Cloud Storage
- Enqueue Cloud Tasks

### `image`

Points to the image in Artifact Registry. We use `app:latest` for now, but GitHub Actions will deploy with a `<git-sha>` tag for rollbacks.

### `ports`

Cloud Run expects port 8080 by default. We explicitly set it.

### `env` from secrets

Instead of `--set-secrets` in `gcloud`, we define env vars from secrets directly in Terraform:

```hcl
env {
  name = "DATABASE_URL"
  value_from {
    secret_key_ref {
      name = "DATABASE_URL"
      secret_key = "latest"
    }
  }
}
```

### `min_scale = 0` (scale to zero)

When there's no traffic, Cloud Run scales to zero instances. This means no cost. The first request after idle takes 1-2 seconds to start (cold start).

### `max_scale = 5`

Hard cap on instances. Prevents runaway scaling from a traffic spike.

### `timeout = "60s"`

Max duration for a single request. If a request takes longer, Cloud Run kills it.

### `resources`

CPU and memory limits. Django with Gunicorn typically needs 512Mi and 1 CPU.

---

## Update image after GitHub Actions builds

After GitHub Actions builds and pushes the image with a `<git-sha>` tag, we update Cloud Run:

```bash
gcloud run services update mycoolproject \
  --image=southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:<git-sha> \
  --region=southamerica-east1
```

Or in Terraform, we can set the image dynamically, but it's common to manage the deployed image tag via GitHub Actions (not Terraform) since Terraform apply is slow and GitHub Actions deploys on every push.

---

## Health check endpoint

Cloud Run needs a health check to know if the container is running. Django should have a `/health/` endpoint that returns `{"status": "ok"}`.

In `web/core/urls.py`:

```python
from django.http import JsonResponse

urlpatterns = [
    # ... other routes ...
    path("health/", lambda request: JsonResponse({"status": "ok"})),
]
```

---

## Update on deploy

When you push code, GitHub Actions:
1. Builds Docker image
2. Pushes to Artifact Registry with `<git-sha>` tag
3. Updates Cloud Run to use the new image

```bash
gcloud run services update mycoolproject \
  --image=<registry-url>/app:<git-sha> \
  --region=southamerica-east1
```

Cloud Run creates a new revision and gradually shifts traffic (or shifts all at once for simplicity in this guide).

---

## Verify the service

```bash
# Get the service URL
gcloud run services describe mycoolproject --region=southamerica-east1 --format="value(status.url)"

# Test it
curl <url>/health/
```

---

## Navigation



- [01 — Introduction: What We're Building](01_introduction.md)
- [02 — Terraform Overview](02_terraform_overview.md)
- [03 — Cloud Services Explained](03_cloud_services.md)
- [04 — PlanetScale Database Explained](04_planetscale.md)
- [05 — Project Setup & Terraform State](05_project_setup.md)
- [06 — GCP Project & APIs](06_gcp_project.md)
- [07 — Artifact Registry](07_artifact_registry.md)
- [08 — PlanetScale Database](08_planetscale_db.md)
- [09 — Secret Manager](09_secrets.md)
- [10 — Cloud Storage](10_storage.md)
- [11 — Service Accounts & IAM](11_iam.md)
- 12 — Cloud Run (Current chapter)
- [13 — Cloud Tasks & Scheduler](13_tasks.md)
- [14 — Dockerfile](14_dockerfile.md)
- [15 — First Deploy](15_first_deploy.md)
- [16 — Custom Domain & SSL](16_domain_ssl.md)
- [17 — Workload Identity Federation](17_wif.md)
- [18 — GitHub Actions CI/CD](18_github_actions.md)
- [19 — Quick Reference](19_quick_reference.md)