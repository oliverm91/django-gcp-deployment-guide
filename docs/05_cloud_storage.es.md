---
description: "Step 5: Configure Google Cloud Storage buckets to handle static files and user-uploaded media seamlessly via Django-storages."
image: assets/social-banner.png
---
# 05 — Cloud Storage (Media & Static Files)

← [Anterior: 04 — Secret Manager](04_secret_manager.md)

> ✅ **Practically free at launch.** First 5 GB/month of regional storage is free. Static files (CSS, JS, icons) are ~2–3 MB total. Media files grow with user uploads — a marketplace with a few hundred listings stays well within the free tier. After 5 GB, storage costs ~$0.023/GB/month and egress (serving files to users) costs ~$0.08/GB/month.

## What is Cloud Storage?

Cloud Storage (GCS) is Google's object storage service — like Amazon S3. Files are stored as objects in buckets (flat namespaces, not directories). It's durable (99.999999999% durability), globally accessible, and cheap.

## Why not store files on the container?

Cloud Run containers are **ephemeral** — they start and stop on demand, and multiple instances can run simultaneously. Any file written to the container's local filesystem is lost when the container stops. Media files (user-uploaded images) and static files (CSS, JS, icons) must live outside the container.

## Two buckets

| Bucket | Contents | Access |
|---|---|---|
| `mycoolproject-static` | CSS, JS, icons, OG images — built by `collectstatic` | Public (anyone can read) |
| `mycoolproject-media` | User-uploaded listing images, avatars | Public (served directly via URL) |

---

## Create the buckets

Run in your **local terminal**:

```bash
# Creates the two GCS buckets. Bucket names are globally unique across all of GCP.
# -l sets the region — same region as Cloud Run avoids egress costs.
# Result: visible at console.cloud.google.com/storage/browser
gsutil mb -l southamerica-east1 gs://mycoolproject-media
gsutil mb -l southamerica-east1 gs://mycoolproject-static

# Grants public read access to static files (CSS, JS, icons).
# Without this, browsers would get a 403 when loading the site's stylesheets.
gsutil iam ch allUsers:objectViewer gs://mycoolproject-static

# Grants public read access to media files (user-uploaded listing images, avatars).
# Without this, uploaded images would not display in listings.
gsutil iam ch allUsers:objectViewer gs://mycoolproject-media
```

> `gsutil` is part of the `gcloud` CLI.

---

## Configure Django to use GCS

### Install django-storages

`django-storages` is a Django library that replaces the default file storage backend with cloud providers (GCS, S3, Azure, etc.).

```bash
# Adds django-storages with the Google Cloud Storage backend.
# [google] installs the google-cloud-storage dependency needed to talk to GCS.
# This updates pyproject.toml and uv.lock — commit both files after running.
cd web
uv add django-storages[google]
```

This adds `django-storages` and `google-cloud-storage` to `pyproject.toml`. The `[google]` extra installs the GCS-specific dependencies.

### Settings in `prod.py`

The following goes in `web/core/settings/prod.py`. It only applies in production — local dev still uses the local filesystem.

```python
# web/core/settings/prod.py

STORAGES = {
    # Default storage: where FileField/ImageField uploads go (user media)
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {"bucket_name": "mycoolproject-media"},
    },
    # Static files storage: where collectstatic puts files
    "staticfiles": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": "mycoolproject-static",
            "default_acl": None,
            "object_parameters": {"cache_control": "public, max-age=31536000"},
        },
    },
}

GS_PROJECT_ID = "mycoolproject-prod"
STATIC_URL = "https://storage.googleapis.com/mycoolproject-static/"
MEDIA_URL  = "https://storage.googleapis.com/mycoolproject-media/"
```

`cache_control: public, max-age=31536000` tells browsers to cache static files for 1 year — since `collectstatic` generates content-hashed filenames, stale caches are never an issue.

### How does Django write to GCS without credentials?

The Cloud Run container runs as `mycoolproject-run-sa` (the service account from chapter 01), which has `roles/storage.objectAdmin`. Google's client libraries automatically pick up the service account's identity from the container's metadata server — no credentials file needed.

---

## Collect static files

### Static files vs media files

**Static files** (CSS, JS, icons) are part of your **codebase** — they're the same for all users and only change when you deploy new code. They must be uploaded to GCS before the first deploy so browsers can load the styles when visiting the site.

**Media files** (user-uploaded images, avatars) are created at **runtime** by users. They're uploaded directly by the app when users submit forms — no separate "collection" step needed. Django writes them to GCS automatically via the `storages` backend.

### How the command works

```bash
# Sets an environment variable for this command execution only, then runs collectstatic.
# DJANGO_SETTINGS_MODULE=core.settings.prod tells Django to load prod.py settings,
# which configures the GCS backend so collectstatic knows to upload to gs://mycoolproject-static.
# --noinput skips prompts (useful for automation).
# Result: Django gathers all CSS/JS/icons, adds content hashes, and uploads to GCS
# (the upload happens automatically via the storages backend — no gcloud/gsutil needed).
cd web
DJANGO_SETTINGS_MODULE=core.settings.prod uv run manage.py collectstatic --noinput
```

**What happens behind the scenes:**

1. Django loads `prod.py` settings (because `DJANGO_SETTINGS_MODULE` points to it)
2. Reads the `STORAGES["staticfiles"]` config, which specifies the GCS backend and bucket name
3. Scans all `static/` directories in the project
4. Processes files (minifies CSS/JS, adds content hashes to filenames)
5. The `django-storages` GCS backend automatically uploads them to `gs://mycoolproject-static/`
6. No explicit `gcloud` or `gsutil` commands needed — the backend handles it

After this runs, `https://storage.googleapis.com/mycoolproject-static/` serves all CSS, JS, and icons.

### When to run this

Run it **before the first deploy** and after any CSS/JS/icon change:

In subsequent deploys, the GitHub Actions pipeline can run this automatically — add it as a step before the Docker build if needed.

---

## 📖 Navegación

- [01 — GCP Project Setup](01_gcp_setup.md)
- [02 — Artifact Registry](02_artifact_registry.md)
- [03 — Cloud SQL (PostgreSQL Database)](03_cloud_sql.md)
- [04 — Secret Manager](04_secret_manager.md)
- **05 — Cloud Storage (Media & Static Files)** (capítulo actual)
- [06 — Dockerfile](06_dockerfile.md)
- [07 — First Deploy](07_first_deploy.md)
- [08 — Custom Domain & SSL](08_domain_ssl.md)
- [09 — Workload Identity Federation (Keyless GitHub Actions Auth)](09_workload_identity.md)
- [10 — GitHub Actions CI/CD Pipeline](10_github_actions.md)
- [11 — Quick Reference](11_quick_reference.md)
