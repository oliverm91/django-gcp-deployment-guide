---
description: "A comprehensive guide to deploying a Django web application using Terraform, covering cloud infrastructure, containerized deployment, and automated CI/CD."
image: assets/social-banner.png
---

# Django Deployment Guide — Terraform Edition

Welcome! This guide teaches you how to deploy a Django web application to the cloud using **Terraform** to manage all infrastructure as code.

By the end, you'll have an automated pipeline where every push to GitHub automatically builds, tests, and deploys your app — with zero manual steps.

## Infrastructure as code

All cloud infrastructure in this guide is defined in **Terraform** configuration files. Instead of clicking around a web console or running manual CLI commands, everything lives in version-controlled files.

Benefits of this approach:

- **Documented** — your entire infrastructure is in version control
- **Reproducible** — destroy and recreate from scratch reliably
- **Reviewable** — changes are visible in pull requests before applying
- **Portable** — the same configuration language works across cloud providers. Switching from **GCP** to **AWS** or **Azure** requires changing only the provider section; the rest of your infrastructure code stays the same.

The workflow is: write configuration → run `terraform plan` to preview → run `terraform apply` to create.

## What gets built

This guide implements infrastructure on **Google Cloud Platform (GCP)** with a **PlanetScale** Postgres database.

Your app runs as a **Docker container** on a serverless container platform. It scales to zero when idle (no cost), scales up automatically under load, and handles HTTPS automatically.

The infrastructure consists of:

- **Container platform** — runs your Django app as a Docker container
- **Background job queue** — handles async work (sending emails, processing data)
- **Scheduled tasks** — triggers background jobs on a cron-like schedule
- **Object storage** — static files (CSS, JS) and user-uploaded media
- **Container registry** — private storage for Docker images
- **Secrets management** — credentials stored securely, injected at runtime
- **Managed Postgres** — serverless database with branching workflow
- **GitHub Actions** — CI/CD pipeline for automated deploys
- **Workload Identity** — secure keyless auth from GitHub to your cloud

## Architecture

```
GitHub push
    │
    └── GitHub Actions (CI/CD)
              │
              ├── Run tests
              ├── Build Docker image
              ├── Push to Container Registry
              │
              ▼
         Container Platform (web)
              │
              ├── Reads secrets from Secrets Manager
              ├── Reads/writes files to Object Storage
              ├── Connects to managed Postgres
              └── Dispatches background work to Job Queue
                        │
                        ▼
                   Background Job Queue
                        │
                        ▼
                   Job Worker (separate container)
```

## Chapters

The guide is structured in three parts:

### Part 1 — Foundations (no code yet)

1. [Introduction — What We're Building](01_introduction.md)
2. [Terraform Overview](02_terraform_overview.md)
3. [Cloud Services Explained](03_cloud_services.md)
4. [Managed Postgres Explained](04_planetscale.md)

### Part 2 — Infrastructure with Terraform

5. [Project Setup & Terraform State](05_project_setup.md)
6. [Cloud Project & APIs](06_gcp_project.md)
7. [Container Registry](07_artifact_registry.md)
8. [Secrets Management](09_secrets.md)
9. [Object Storage](10_storage.md)
10. [Service Accounts & IAM](11_iam.md)
12. [Container Platform](12_cloud_run.md)
13. [Background Jobs & Scheduler](13_tasks.md)

### Part 3 — Deployment & Automation

14. [Dockerfile](14_dockerfile.md)
15. [First Deploy](15_first_deploy.md)
16. [Custom Domain & SSL](16_domain_ssl.md)
17. [Workload Identity Federation](17_wif.md)
18. [GitHub Actions CI/CD](18_github_actions.md)
19. [Quick Reference](19_quick_reference.md)

---

## Prerequisites

- A GitHub repository with your Django project
- A cloud account (GCP used in this guide — new accounts get $300 free credits)
- A managed Postgres account (PlanetScale used in this guide — paid plans start at $5/mo)
- `gcloud` CLI installed and authenticated (for GCP)
- Docker installed locally
- Terraform installed

---

## Cost overview

This guide uses GCP and PlanetScale. Costs below reflect those services:

| Service | Free tier | Cost after free tier |
|---|---|---|
| Container platform | 2M requests + 360K CPU GB-s/month | ~$0.00004/request |
| Container registry | 0.5 GB/month | $0.10/GB/month |
| Secrets management | 6 secrets + 10K accesses/month | $0.06/secret/month |
| Object storage | 5 GB/month | ~$0.023/GB/month |
| Background jobs | Free up to 1M actions/month | $0.40/million |
| Task scheduler | 3 jobs free/month | $0.10/job/month |
| GitHub Actions | 2,000 min/month (private repo) | $0.008/min |
| Workload Identity | Unlimited | Free |
| Managed Postgres | No free plan | **$5/mo** for single-node Postgres |
| SSL certificate | Free (managed) | — |

> **PlanetScale** has no free plan. All databases require a paid subscription. Single-node Postgres starts at **$5/month**.

### Low-traffic cost estimation

For a hobby project or low-traffic site with scale-to-zero enabled:

| Service | Monthly cost |
|---|---|
| Container platform | $0 (within free tier) |
| Container registry | $0 (within free tier) |
| Secrets management | $0 (within free tier) |
| Object storage | ~$1 (5 GB static + 1 GB media) |
| Background jobs | $0 (within free tier) |
| Task scheduler | $0.30 (3 jobs, first 3 free) |
| GitHub Actions | $0 (within free tier) |
| Managed Postgres | **$5** |
| **Total** | **~$6–7/mo** |

Cloud Run's scale-to-zero means you pay nothing when there's no traffic. Costs above apply to a site with light background job activity.

## Project introduction
[Introduction — What We're Building](01_introduction.md)