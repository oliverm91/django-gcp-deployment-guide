# 01 — GCP Project Setup

> ✅ **This chapter is free.** Project creation, API enablement, and service accounts have no cost.
>
> 💳 **Requires a billing account.** GCP requires a credit card to create a billing account, even to use free-tier services. Link a billing account at [console.cloud.google.com/billing](https://console.cloud.google.com/billing). New accounts receive **$300 in free credits** valid for 90 days — enough to run this entire stack for months before paying anything.

## What is a GCP Project?

A **Google Cloud Platform** (GCP) project is an isolated container for all your cloud resources — databases, servers, storage buckets, and billing. Everything you create in this guide lives inside one project. You can have multiple projects (e.g. `mycoolproject-prod` and `mycoolproject-staging`) with completely separate resources and billing.

## What is the gcloud CLI?

`gcloud` is Google's command-line tool for managing GCP resources. You run it in your local terminal. It talks to GCP's APIs on your behalf. Install it from [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install).

All commands below run **in your local terminal** (not inside Django, not inside Docker). Use bash, WSL2, or PowerShell depending on your platform — `gcloud` works identically on all.

---

## Create the project

```bash
# Opens a browser to authenticate your local gcloud CLI with your Google account.
# Required once per machine before any other gcloud command will work.
# Result: gcloud prints "You are now logged in as <email>"
gcloud auth login

# Creates a new GCP project named mycoolproject-prod.
# All resources (database, containers, storage) will live inside this project.
# Result: visible at console.cloud.google.com/home/dashboard?project=mycoolproject-prod
gcloud projects create mycoolproject-prod --name="MyCoolProject Prod"

# Sets mycoolproject-prod as the default project for all subsequent gcloud commands.
# Without this you'd need --project=mycoolproject-prod on every command.
gcloud config set project mycoolproject-prod

# Sets the default region so you don't need --region= on every command.
# southamerica-east1 (São Paulo) is the closest GCP region to Chile.
gcloud config set run/region southamerica-east1
```

> **Region:** `southamerica-east1` is São Paulo — the closest GCP region to Chile (~30–60 ms latency to Santiago). All resources in this guide use this region for consistency.

---

## Enable APIs

GCP services are disabled by default — you enable only what you need. This is a one-time step per project.

```bash
# Enables all GCP APIs this project needs. APIs are disabled by default — nothing
# works until you enable it. This is a one-time step per project.
# Result: each API listed at console.cloud.google.com/apis/dashboard
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  storage.googleapis.com \
  iamcredentials.googleapis.com
```

What each API does:

| API | Enables |
|---|---|
| `run.googleapis.com` | Cloud Run (runs the Django container) |
| `sqladmin.googleapis.com` | Cloud SQL (PostgreSQL database) |
| `secretmanager.googleapis.com` | Secret Manager (credentials storage) |
| `artifactregistry.googleapis.com` | Artifact Registry (Docker image storage) |
| `storage.googleapis.com` | Cloud Storage (media + static files) |
| `iamcredentials.googleapis.com` | Workload Identity (keyless GitHub Actions auth) |

---

## Create a Service Account

### What is a Service Account?

A service account is an identity for a program (not a person). Instead of your Cloud Run container running as you (the developer), it runs as a dedicated account with only the permissions it needs. This limits the blast radius if the app is ever compromised.

```bash
# Creates a service account — an identity for the Cloud Run container to run as.
# Using a dedicated account (not your personal account) limits blast radius if compromised.
# Result: visible at console.cloud.google.com/iam-admin/serviceaccounts
gcloud iam service-accounts create mycoolproject-run-sa \
  --display-name="MyCoolProject Cloud Run SA"
```

This creates the identity `mycoolproject-run-sa@mycoolproject-prod.iam.gserviceaccount.com`.

### What are IAM Roles?

IAM (Identity and Access Management) roles are sets of permissions. You assign roles to identities (users or service accounts). Instead of giving broad admin access, you give only what's needed:

```bash
SA="mycoolproject-run-sa@mycoolproject-prod.iam.gserviceaccount.com"

# Grants the service account permission to connect to Cloud SQL via the proxy socket.
# Without this, the container cannot reach the database at runtime.
# Result: visible at console.cloud.google.com/iam-admin/iam (filter by service account)
gcloud projects add-iam-policy-binding mycoolproject-prod \
  --member="serviceAccount:$SA" \
  --role="roles/cloudsql.client"

# Grants permission to read secrets from Secret Manager.
# Without this, Cloud Run can't fetch DATABASE_URL, SECRET_KEY, etc. at startup.
gcloud projects add-iam-policy-binding mycoolproject-prod \
  --member="serviceAccount:$SA" \
  --role="roles/secretmanager.secretAccessor"

# Grants permission to read and write objects in Cloud Storage buckets.
# Needed for collectstatic (write) and serving user-uploaded media files (read).
gcloud projects add-iam-policy-binding mycoolproject-prod \
  --member="serviceAccount:$SA" \
  --role="roles/storage.objectAdmin"
```

The Cloud Run container will use this service account at runtime — it automatically has these permissions without any credentials file.

---

## 📖 Navigation

- **01 — GCP Project Setup** (current chapter)
- [02 — Artifact Registry](02_artifact_registry.md)
- [03 — Cloud SQL (PostgreSQL Database)](03_cloud_sql.md)
- [04 — Secret Manager](04_secret_manager.md)
- [05 — Cloud Storage (Media & Static Files)](05_cloud_storage.md)
- [06 — Dockerfile](06_dockerfile.md)
- [07 — First Deploy](07_first_deploy.md)
- [08 — Custom Domain & SSL](08_domain_ssl.md)
- [09 — Workload Identity Federation (Keyless GitHub Actions Auth)](09_workload_identity.md)
- [10 — GitHub Actions CI/CD Pipeline](10_github_actions.md)
- [11 — Quick Reference](11_quick_reference.md)
