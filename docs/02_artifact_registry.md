---
description: "Create a private Docker Artifact Registry in GCP to tightly control and store your containerized Django app images."
image: assets/social-banner.png
---
# 02 — Artifact Registry

← [Previous: 01 — GCP Project Setup](01_gcp_setup.md)

> ✅ **Practically free.** First 0.5 GB of storage per month is free. A typical Django image is ~200–300 MB, so early on you stay within the free tier. After that, storage costs $0.10/GB/month. Network traffic between Artifact Registry and Cloud Run in the same region is free.

## What is Artifact Registry?

Artifact Registry is GCP's private container image registry — the place where Docker images are stored before they're deployed. Think of it like Docker Hub, but private and inside your GCP project.

When [GitHub Actions builds a Docker image from your code](10_github_actions.md), it pushes it here. When Cloud Run deploys, it pulls the image from here. The image never leaves GCP's network.

## What is a Docker image?

A Docker image is a packaged, self-contained snapshot of your application: the Python runtime, all dependencies, your Django code, and the command to start the server — all bundled into a single file. Cloud Run takes this image and runs it as a container (a live process).

---

## Create the repository

```bash
# Creates a private Docker image registry inside your GCP project.
# This is where GitHub Actions will push built images and Cloud Run will pull from.
# Result: visible at console.cloud.google.com/artifacts — the registry URL will be
# southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/
gcloud artifacts repositories create mycoolproject-repo \
  --repository-format=docker \
  --location=southamerica-east1
```

This creates a repository at:
```
southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/
```

Images pushed here will be named:
```
southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/app:<tag>
```

Tags used in this guide:
- `latest` — always points to the most recent build
- `<git-sha>` — e.g. `a3f9c12` — unique tag per commit, used for precise rollbacks

## Authenticate Docker to push images

Before pushing images from your local machine (first deploy only — GitHub Actions handles this automatically afterwards):

```bash
# Configures Docker on your local machine to use gcloud credentials when pushing
# to this registry. Run once per machine — not needed in GitHub Actions (handled
# by the workflow). Writes a credential helper to ~/.docker/config.json.
gcloud auth configure-docker southamerica-east1-docker.pkg.dev
```

This updates your local Docker config so it knows to use `gcloud` credentials when pushing to this registry.

---

## 📖 Navigation

- [01 — GCP Project Setup](01_gcp_setup.md)
- **02 — Artifact Registry** (current chapter)
- [03 — Cloud SQL (PostgreSQL Database)](03_cloud_sql.md)
- [04 — Secret Manager](04_secret_manager.md)
- [05 — Cloud Storage (Media & Static Files)](05_cloud_storage.md)
- [06 — Dockerfile](06_dockerfile.md)
- [07 — First Deploy](07_first_deploy.md)
- [08 — Custom Domain & SSL](08_domain_ssl.md)
- [09 — Workload Identity Federation (Keyless GitHub Actions Auth)](09_workload_identity.md)
- [10 — GitHub Actions CI/CD Pipeline](10_github_actions.md)
- [11 — Quick Reference](11_quick_reference.md)
