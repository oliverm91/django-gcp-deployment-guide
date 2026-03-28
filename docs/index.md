---
description: "A comprehensive guide to deploying a Django web application on Google Cloud Platform using Cloud Run, Cloud SQL, and GitHub Actions."
image: assets/social-banner.png
---
# Django Deployment guide using GCP

This guide walks through deploying MyCoolProject (a Django project) to Google Cloud Platform using a fully automated CI/CD pipeline.

> **Platform note:** This guide uses **Linux/Mac command syntax** (e.g., `/dev/mycoolproject/`, `export VAR=value`, `echo -n`). If you're on **Windows**, use PowerShell equivalents (e.g., `C:\dev\mycoolproject\`, `$env:VAR=value`). When a chapter first mentions a platform-specific difference, it will explain the Windows alternative once. From that point on, examples show Linux/Mac syntax — just remember to adapt paths and shell syntax as needed.

---

## What gets deployed

For the sake of examples, MyCoolProject is a Django web application, **but most of the concepts apply to any web application**. In production it runs as a **Docker container** on **Cloud Run** — Google's serverless container platform. Every push to the `main` branch automatically runs tests, builds a new container image, and deploys it.

## Architecture

![Architecture](architecture.svg)

## Services used

| Service | What it does |
|---|---|
| **Cloud Run** | Runs the Django app as a container. Scales to zero when idle, scales up under load. Handles HTTPS automatically. |
| **Artifact Registry** | Stores Docker images. Like Docker Hub but private and inside GCP. |
| **Cloud SQL** | Managed PostgreSQL database. Google handles backups, patches, and availability. |
| **Secret Manager** | Stores credentials (DB password, secret key, API keys). Injected into the container at runtime — never stored in code or environment files. |
| **Cloud Storage (GCS)** | Object storage for user-uploaded images and Django's collected static files. |
| **GitHub Actions** | Runs the CI/CD pipeline on every push. Free for 2,000 minutes/month. |
| **Workload Identity Federation** | Lets GitHub Actions authenticate to GCP without storing long-lived credentials in GitHub secrets. |

## Chapters

The guide is ordered by **setup dependency** — each chapter sets up infrastructure the next one needs. But the everyday development flow is the reverse: you push code → GitHub Actions → builds image → deploys to Cloud Run → reads from the infrastructure below.

### Setup order (follow this when deploying for the first time)

1. [GCP Project Setup](01_gcp_setup.md) — project, APIs, service account
2. [Artifact Registry](02_artifact_registry.md) — where Docker images are stored
3. [Cloud SQL — Database](03_cloud_sql.md) — PostgreSQL, migrations
4. [Secret Manager](04_secret_manager.md) — credentials, API keys
5. [Cloud Storage — Media & Static Files](05_cloud_storage.md) — uploads, CSS/JS
6. [Dockerfile](06_dockerfile.md) — packaging the app as a container
7. [First Deploy](07_first_deploy.md) — manual deploy to verify everything works
8. [Custom Domain & SSL](08_domain_ssl.md) — mycoolproject.cl, HTTPS
9. [Workload Identity — Keyless Auth](09_workload_identity.md) — GitHub → GCP auth without keys
10. [GitHub Actions — CI/CD Pipeline](10_github_actions.md) — automates all of the above on every push
11. [Quick Reference](11_quick_reference.md) — all commands in one place

### Everyday development flow (once deployed)

![Workflow Diagram](workflow.svg)

> **💡 Note on Deployments:** Opening or updating a Pull Request will **only run your tests** to ensure the code is healthy. The actual deployment steps (Build, Migrate, Deploy) only execute when code is officially **merged/pushed** to the `main` branch.

## Cost overview

> **New GCP accounts get $300 free credits** — enough to run everything for months before paying anything.

| Service | Free tier | Cost after free tier |
|---|---|---|
| Cloud Run | 2M requests + 360K CPU GB-s/month | ~$0.00004/request |
| Artifact Registry | 0.5 GB storage/month | $0.10/GB/month |
| Secret Manager | 6 secret versions + 10K accesses/month | $0.06/version/month |
| Cloud Storage | 5 GB/month | ~$0.023/GB/month |
| GitHub Actions | 2,000 min/month (private repo) | $0.008/min |
| Workload Identity | Unlimited | Free |
| **Cloud SQL** | ❌ **No free tier** | **~$7–10/month always running** |
| Custom domain | — | ~$10–15/year at your registrar |
| SSL certificate | Free (managed by GCP) | — |

**Cloud SQL is the only service that starts billing immediately and continuously.** Set it up last — right before go-live — to minimise idle spend.

### Recommended setup order to minimise cost

Do these first — all free:
- Chapters 01, 02, 04, 09, 10 (GCP project, Artifact Registry, Secret Manager, Workload Identity, GitHub Actions)

Then nearly free:
- Chapters 05, 06, 07 (Cloud Storage, Dockerfile, Cloud Run deploy)

Then when ready to go live (starts costing money):
- Chapter 03 — Cloud SQL (~$7–10/month from the moment it's created)
- Chapter 08 — Custom domain (~$10–15/year, paid to your registrar)

---

## Prerequisites

- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated (`gcloud auth login`)
- Docker installed locally (for the first manual deploy)
- A GCP account (new accounts get $300 free credits)
- A GitHub repository with the MyCoolProject codebase

---

## 📖 Chapters

- [01 — GCP Project Setup](01_gcp_setup.md)
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
