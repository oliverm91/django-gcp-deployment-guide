---
description: "Create Cloud Storage buckets for static files and media uploads using Terraform."
image: assets/social-banner.png
---

# 10 — Cloud Storage

← [Previous: 09 — Secret Manager](09_secrets.md)

Cloud Storage (GCS) stores static files and user-uploaded media. We'll create two buckets with Terraform: one for static files (CSS, JS) and one for media (user uploads).

---

## Why two buckets?

| Bucket | Contents | Who writes | Who reads |
|---|---|---|---|
| `static` | CSS, JS, icons — from `collectstatic` | Django (at deploy time) | Browsers directly |
| `media` | User-uploaded images, avatars | Django (at runtime) | Browsers directly |

Both are publicly readable so browsers can fetch files directly without going through Django.

---

## Create the buckets with Terraform

Add to `infrastructure/main.tf`:

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

  # CORS for font loading from web fonts (if needed)
  # cors {
  #   origin          = ["https://mycoolproject.com"]
  #   method          = ["GET"]
  #   response_header = ["Content-Type"]
  #   max_age_seconds = 3600
  # }
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

Run `terraform apply` to create both buckets.

---

## What gets created

| Bucket name | URL | Purpose |
|---|---|---|
| `mycoolproject-prod-static` | `https://storage.googleapis.com/mycoolproject-prod-static/` | CSS, JS, fonts |
| `mycoolproject-prod-media` | `https://storage.googleapis.com/mycoolproject-prod-media/` | User uploads |

---

## Django configuration

In `web/core/settings/prod.py`:

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

## Collectstatic: upload static files

Before deploying, run `collectstatic` to upload CSS, JS, and fonts to GCS:

```bash
cd web
DJANGO_SETTINGS_MODULE=core.settings.prod uv run manage.py collectstatic --noinput
```

This uploads all static files to the static bucket. Django's GCS backend handles this automatically via the `storages` library.

---

## No media files to collect

Media files (user uploads) are uploaded at runtime when users submit forms. There's no `collectstatic` equivalent — Django writes directly to GCS via the `storages` backend.

---

## Verify buckets exist

```bash
gsutil ls
```

You should see:
```
gs://mycoolproject-prod-static/
gs://mycoolproject-prod-media/
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
- [08 — Secrets Management](09_secrets.md)
- 09 — Cloud Storage (Current chapter)
- [10 — Service Accounts & IAM](11_iam.md)
- [11 — Cloud Run](12_cloud_run.md)
- [12 — Cloud Tasks & Scheduler](13_tasks.md)
- [13 — Dockerfile](14_dockerfile.md)
- [14 — First Deploy](15_first_deploy.md)
- [15 — Custom Domain & SSL](16_domain_ssl.md)
- [16 — Workload Identity Federation](17_wif.md)
- [17 — GitHub Actions CI/CD](18_github_actions.md)
- [18 — Quick Reference](19_quick_reference.md)