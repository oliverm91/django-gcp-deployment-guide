---
description: "Understand what we're building and why — a cloud-native Django app with automated deployment."
image: assets/social-banner.png
---

# 01 — Introduction: What We're Building

This guide teaches you how to deploy a Django web application to the cloud. By the end, you'll have an automated pipeline where every push to GitHub automatically builds, tests, and deploys your app.

---

## What we're building

A production-ready Django web application running on Google Cloud Platform (GCP), using:

- **Terraform** to manage all infrastructure as code
- **Cloud Run** to run your Docker container (serverless, scales to zero)
- **PlanetScale** for the managed Postgres database
- **Cloud Tasks** for background job processing
- **GitHub Actions** for automated CI/CD

---

## The problem we solve

Before this guide:
1. You click around a cloud console to create resources
2. You run CLI commands to deploy
3. You hope nothing breaks and you remember all the steps

After this guide:
1. You write Terraform files describing what you want
2. You push to GitHub
3. Everything happens automatically

---

## Who this guide is for

- Django developers who want to deploy to production
- Developers new to cloud infrastructure (GCP, AWS, etc.)
- Anyone tired of manual, error-prone deployment processes

No prior cloud or Terraform experience required.

---

## What you'll learn

- How Terraform works and why it's better than manual commands
- How each cloud service fits into the overall architecture
- How to set up a complete infrastructure using Terraform
- How to containerize a Django application with Docker
- How to automate deployment with GitHub Actions
- How to connect a custom domain with free SSL

---

## The big picture

```
GitHub push
    │
    └── GitHub Actions
              │
              ├── Run tests
              ├── Build Docker image
              ├── Push to Container Registry
              │
              ▼
         Cloud Run (web)
              │
              ├── Reads secrets from Secret Manager
              ├── Reads/writes to Cloud Storage
              ├── Connects to PlanetScale (Postgres)
              └── Dispatches work to Cloud Tasks
                        │
                        ▼
              Cloud Tasks queue + worker
```

---

## Services explained

### Container platform — Cloud Run

Your Django app runs as a **Docker container** on Cloud Run. It's serverless — scales to zero when idle, scales up automatically under load, handles HTTPS automatically.

In this guide: **Cloud Run** (GCP)

### Background jobs — Cloud Tasks

Some tasks are too slow to run inside a web request (sending emails, generating PDFs). Cloud Tasks lets you enqueue these jobs and process them in the background.

In this guide: **Cloud Tasks** (GCP)

### Scheduled tasks — Cloud Scheduler

Cloud Scheduler triggers background jobs on a cron-like schedule (e.g., "check every minute for due tasks").

In this guide: **Cloud Scheduler** (GCP)

### Object storage — Cloud Storage

Static files (CSS, JS) and user uploads go here, not on the container filesystem.

In this guide: **Cloud Storage** (GCP)

### Container registry — Artifact Registry

Docker images are stored here, not on Docker Hub. Private, inside your cloud project.

In this guide: **Artifact Registry** (GCP)

### Secrets management — Secret Manager

Passwords, API keys, connection strings — stored securely, injected at runtime.

In this guide: **Secret Manager** (GCP)

### Managed Postgres — Database

A database that's fully managed — no server maintenance, backups are handled automatically, and it scales serverlessly. The connection is a standard Postgres connection string.

In this guide: **PlanetScale** (serverless Postgres with branching workflow)

### GitHub Actions — CI/CD

GitHub Actions runs your pipeline on every push:
1. Run tests
2. Build Docker image
3. Push to container registry
4. Run any migration or setup jobs
5. Deploy the new version

### Workload Identity — Secure auth

Workload Identity lets GitHub Actions authenticate to GCP without storing JSON keys — more secure, no manual rotation needed.

In this guide: **Workload Identity Federation** (GCP)

---

## Navigation



- 01 — Introduction: What We're Building (Current chapter)
- [02 — Terraform Overview](02_terraform_overview.md)
- [03 — Cloud Services Explained](03_cloud_services.md)
- [04 — PlanetScale Database Explained](04_planetscale.md)
- [05 — Project Setup & Terraform State](05_project_setup.md)
- [06 — GCP Project & APIs](06_gcp_project.md)
- [07 — Artifact Registry](07_artifact_registry.md)
- [08 — Secrets Management](09_secrets.md)
- [09 — Cloud Storage](10_storage.md)
- [10 — Service Accounts & IAM](11_iam.md)
- [11 — Cloud Run](12_cloud_run.md)
- [12 — Cloud Tasks & Scheduler](13_tasks.md)
- [13 — Dockerfile](14_dockerfile.md)
- [14 — First Deploy](15_first_deploy.md)
- [15 — Custom Domain & SSL](16_domain_ssl.md)
- [16 — Workload Identity Federation](17_wif.md)
- [17 — GitHub Actions CI/CD](18_github_actions.md)
- [18 — Quick Reference](19_quick_reference.md)