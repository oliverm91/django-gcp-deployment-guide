---
description: "Build a fully automated CI/CD pipeline using GitHub Actions that tests, builds, and deploys your Django app on every push."
image: assets/social-banner.png
---

# 18 — GitHub Actions CI/CD

← [Previous: 17 — Workload Identity Federation](17_wif.md)

This chapter creates the GitHub Actions workflow that automates the entire deploy process. Every push to `main` will automatically run tests, build the Docker image, push it to Artifact Registry, run migrations, and deploy to Cloud Run.

---

## What we want to happen

On **every push to `main`**:
1. Run tests
2. Build Docker image
3. Push to Artifact Registry (two tags: `latest` + `<git-sha>`)
4. Run database migrations on PlanetScale
5. Deploy to Cloud Run

On **every pull request**:
1. Run tests only (no deploy)

---

## Create the workflow file

Create `.github/workflows/deploy.yml` at the repo root:

```yaml
name: Test & Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGION: southamerica-east1
  IMAGE: southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app

jobs:
  # ── Job 1: test ─────────────────────────────────────────────────────────────
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: astral-sh/setup-uv@v4
        with:
          working-directory: web

      - name: Install dependencies
        run: cd web && uv sync --frozen

      - name: Run tests
        run: cd web && uv run manage.py test web/tests --settings=core.settings.test
        env:
          SECRET_KEY: ci-secret-not-real

  # ── Job 2: deploy ────────────────────────────────────────────────────────────
  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'

    permissions:
      contents: read
      id-token: write

    steps:
      - uses: actions/checkout@v4

      # Authenticate to GCP using Workload Identity
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}

      # Install gcloud CLI
      - uses: google-github-actions/setup-gcloud@v2

      # Configure Docker to push to Artifact Registry
      - name: Configure Docker
        run: gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev --quiet

      # Build image with two tags
      - name: Build image
        run: |
          docker build \
            -t ${{ env.IMAGE }}:${{ github.sha }} \
            -t ${{ env.IMAGE }}:latest \
            .

      # Push both tags
      - name: Push image
        run: docker push --all-tags ${{ env.IMAGE }}

      # Update the Cloud Run service to use the new image
      - name: Deploy to Cloud Run
        run: |
          gcloud run services update mycoolproject \
            --image=${{ env.IMAGE }}:${{ github.sha }} \
            --region=${{ env.REGION }}

      # Run migrations via a Cloud Run Job
      - name: Run migrations
        run: |
          gcloud run jobs execute migrate \
            --region=${{ env.REGION }} \
            --wait
```

---

## How it works step by step

### On push to main

```
push to main
    │
    ├── test job
    │     ├── checkout code
    │     ├── install uv + dependencies
    │     └── run tests
    │               │
    │          fails? → workflow stops, no deploy
    │          passes? ↓
    │
    └── deploy job
          ├── authenticate to GCP (Workload Identity)
          ├── docker build (uses layer cache)
          ├── docker push → Artifact Registry
          └── gcloud run services update → new revision goes live
```

### On pull request

```
PR push
    │
    └── test job
          ├── checkout
          ├── install deps
          └── run tests
                   │
              fails? → PR blocked
              passes? → PR ready to merge
```

The deploy job is skipped because `github.ref` is not `refs/heads/main`.

---

## Workflow permissions

The `permissions` block is important:

```yaml
permissions:
  contents: read      # Read the repo
  id-token: write     # Allow OIDC token exchange (for Workload Identity)
```

`id-token: write` is required for Workload Identity to work — it allows the workflow to exchange an OIDC token for a GCP access token.

---

## Environment variables

```yaml
env:
  REGION: southamerica-east1
  IMAGE: southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app
```

These are workflow-level variables available to all jobs. If you change project/region, update here.

---

## The image tags

We push two tags:

| Tag | Meaning | Used for |
|---|---|---|
| `latest` | Most recent build | Rollbacks, emergency deploys |
| `<git-sha>` | Unique per commit | Precise rollback to specific commit |

Cloud Run is deployed with `<git-sha>` so we can roll back to this exact commit if needed.

---

## Rollback

If a bad deploy goes live, roll back in seconds:

```bash
# List recent images in Artifact Registry
gcloud artifacts docker images list southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app

# Update Cloud Run to use a previous commit's image
gcloud run services update mycoolproject \
  --image=southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:<previous-sha> \
  --region=southamerica-east1
```

Or via GitHub Actions — re-run the previous commit's workflow.

---

## Migrations in the workflow

Migrations run as a Cloud Run Job (`migrate`) that we created in chapter 15. The workflow triggers this job with `--wait` so it completes before traffic moves to the new version.

For PlanetScale, migrations need to be schema changes (create table, add column, etc.) — the `migrate` command handles this.

---

## Secrets in GitHub

Make sure these secrets are set in **GitHub → Settings → Secrets and variables → Actions**:

| Secret | Value |
|---|---|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | From chapter 17 |
| `GCP_SERVICE_ACCOUNT` | `mycoolproject-run@mycoolproject-prod.iam.gserviceaccount.com` |

---

## Verifying the workflow

1. Push a commit to main
2. Go to **GitHub → Actions** tab
3. Watch the workflow run
4. If it succeeds, visit your site URL
5. If it fails, click on the failed job to see logs

---

## Cost

GitHub Actions gives 2,000 free minutes/month for private repos.

Each deploy run takes ~5-10 minutes, so you get ~200-400 free deploys/month.

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
- [12 — Cloud Run](12_cloud_run.md)
- [13 — Cloud Tasks & Scheduler](13_tasks.md)
- [14 — Dockerfile](14_dockerfile.md)
- [15 — First Deploy](15_first_deploy.md)
- [16 — Custom Domain & SSL](16_domain_ssl.md)
- [17 — Workload Identity Federation](17_wif.md)
- 18 — GitHub Actions CI/CD (Current chapter)
- [19 — Quick Reference](19_quick_reference.md)