---
description: "Create service accounts and configure IAM permissions for Cloud Run and other GCP services."
image: assets/social-banner.png
---

# 11 — Service Accounts & IAM

← [Previous: 10 — Cloud Storage](10_storage.md)

Service accounts are identities that Cloud Run and other services use to access other GCP resources. This chapter creates the service account and grants it only the permissions it needs.

---

## Principle of least privilege

We follow the principle of least privilege: give each identity only the permissions it needs, nothing more.

Our Cloud Run web service needs:
- **Secret Manager** — read secrets (DATABASE_URL, SECRET_KEY, etc.)
- **Cloud Storage** — read/write static and media buckets

It does NOT need:
- Cloud SQL Admin (we're not using Cloud SQL)
- Compute Admin (not running VMs)
- Full IAM (too broad)

---

## Create service account with Terraform

Add to `infrastructure/main.tf`:

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

Run `terraform apply` to create the service account and permissions.

---

## Service account email format

The service account email will be:
```
mycoolproject-run@mycoolproject-prod.iam.gserviceaccount.com
```

This format is used throughout Terraform and `gcloud` commands to reference the identity.

---

## Service account for Cloud Tasks worker

The Cloud Tasks worker (Cloud Run Job) needs its own permissions to run Django management commands and access secrets:

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

## IAM roles summary

| Service Account | Role | Why |
|---|---|---|
| `mycoolproject-run` | `secretmanager.secretAccessor` | Read secrets (DB, secret key, etc.) |
| `mycoolproject-run` | `storage.objectAdmin` | Read/write static and media files |
| `mycoolproject-run` | `cloudtasks.admin` | Enqueue tasks from web service |
| `mycoolproject-worker` | `secretmanager.secretAccessor` | Read secrets for background jobs |
| `mycoolproject-worker` | `storage.objectAdmin` | Write processed files if needed |
| `mycoolproject-worker` | `cloudtasks.admin` | Process tasks from queue |

---

## Outputs for service account emails

Add to `main.tf`:

```hcl
output "run_service_account_email" {
  value = google_service_account.run.email
}

output "worker_service_account_email" {
  value = google_service_account.worker.email
}
```

---

## Verify the service accounts

```bash
gcloud iam service-accounts list --project=mycoolproject-prod
```

You should see both `mycoolproject-run` and `mycoolproject-worker`.

---

## What we've built so far

After chapters 05-11, Terraform has created:
- GCP project with APIs enabled
- Artifact Registry repository
- Serverless VPC connector (for PlanetScale)
- Secret Manager secrets (structure, not values)
- Cloud Storage buckets (static + media)
- Service accounts with IAM permissions

Next: Cloud Run service (the actual web server).

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
- 11 — Service Accounts & IAM (Current chapter)
- [12 — Cloud Run](12_cloud_run.md)
- [13 — Cloud Tasks & Scheduler](13_tasks.md)
- [14 — Dockerfile](14_dockerfile.md)
- [15 — First Deploy](15_first_deploy.md)
- [16 — Custom Domain & SSL](16_domain_ssl.md)
- [17 — Workload Identity Federation](17_wif.md)
- [18 — GitHub Actions CI/CD](18_github_actions.md)
- [19 — Quick Reference](19_quick_reference.md)