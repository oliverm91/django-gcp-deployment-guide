---
description: "A quick reference guide for all Terraform commands, gcloud commands, and other useful snippets used throughout this guide."
image: assets/social-banner.png
---

# 19 — Quick Reference

← [Previous: 18 — GitHub Actions CI/CD](18_github_actions.md)

All the important commands from this guide in one place.

---

## Terraform

```bash
cd infrastructure

terraform init               # Initialize (download providers, setup backend)
terraform plan               # Preview changes (no actual changes)
terraform apply              # Apply changes (creates/updates resources)
terraform apply -auto-approve # Apply without confirmation prompt
terraform destroy            # Delete all Terraform-managed resources
terraform show               # Show current state
terraform output             # Show output values
terraform state list         # List all resources in state
terraform refresh            # Sync state with real infrastructure
```

---

## Terraform variables

```bash
# Set a variable via CLI
terraform plan -var="project_id=my-project"

# Or in terraform.tfvars (not committed to git)
echo 'project_id = "my-project"' > terraform.tfvars
```

---

## GCP Project & APIs

```bash
# Get current project
gcloud config get-value project

# Set project
gcloud config set project mycoolproject-prod

# Get project number
gcloud projects describe mycoolproject-prod --format='value(projectNumber)'

# List enabled APIs
gcloud services list --enabled --project=mycoolproject-prod
```

---

## Artifact Registry

```bash
# Authenticate Docker
gcloud auth configure-docker southamerica-east1-docker.pkg.dev

# List repositories
gcloud artifacts repositories list --project=mycoolproject-prod

# List images in a repository
gcloud artifacts docker images list southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo
```

---

## Cloud Run

```bash
# Deploy a new image
gcloud run deploy mycoolproject \
  --image=southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:latest \
  --region=southamerica-east1

# Get service URL
gcloud run services describe mycoolproject --region=southamerica-east1 --format="value(status.url)"

# View logs
gcloud run services logs tail mycoolproject --region=southamerica-east1

# List revisions
gcloud run revisions list --service=mycoolproject --region=southamerica-east1

# Rollback to previous revision
gcloud run services update-traffic mycoolproject \
  --region=southamerica-east1 \
  --to-revisions=mycoolproject-<revision>=100

# Update env vars
gcloud run services update mycoolproject \
  --region=southamerica-east1 \
  --update-env-vars=ALLOWED_HOSTS="mycoolproject.com,www.mycoolproject.com"
```

---

## Cloud Run Jobs

```bash
# Create a job
gcloud run jobs create job-name \
  --image=southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:latest \
  --region=southamerica-east1

# Run a job (and wait)
gcloud run jobs execute job-name --region=southamerica-east1 --wait

# List jobs
gcloud run jobs list --region=southamerica-east1
```

---

## Cloud Tasks

```bash
# List queues
gcloud tasks queues list --location=southamerica-east1

# Purge a queue (delete all tasks)
gcloud tasks queues purge mycoolproject-default --location=southamerica-east1
```

---

## Cloud Scheduler

```bash
# Create a scheduler job (trigger Cloud Run Job)
gcloud scheduler jobs create http worker-trigger \
  --schedule="* * * * *" \
  --uri="https://region-run.googleapis.com/v2/projects/mycoolproject-prod/locations/southamerica-east1/jobs/mycoolproject-worker:run" \
  --http-method=POST \
  --oidc-service-account-email=mycoolproject-scheduler@mycoolproject-prod.iam.gserviceaccount.com

# List jobs
gcloud scheduler jobs list --location=southamerica-east1

# Pause a job
gcloud scheduler jobs pause worker-trigger --location=southamerica-east1

# Resume a job
gcloud scheduler jobs resume worker-trigger --location=southamerica-east1
```

---

## Cloud Storage

```bash
# List buckets
gsutil ls

# List bucket contents
gsutil ls gs://mycoolproject-prod-static/

# Make bucket public
gsutil iam ch allUsers:objectViewer gs://mycoolproject-prod-static

# Upload file
gsutil cp file.txt gs://mycoolproject-prod-media/

# Download file
gsutil cp gs://mycoolproject-prod-media/file.txt ./

# Set cache control on files
gsutil setmeta -h "Cache-Control:public, max-age=31536000" gs://mycoolproject-prod-static/**/*.css
```

---

## Secret Manager

```bash
# List secrets
gcloud secrets list

# Create a secret
echo -n "value" | gcloud secrets create SECRET_NAME --data-file=-

# Add a new version
echo -n "new-value" | gcloud secrets versions add SECRET_NAME --data-file=-

# Read a secret
gcloud secrets versions access latest --secret=SECRET_NAME

# Delete a secret (and all versions)
gcloud secrets delete SECRET_NAME
```

---

## Service Accounts

```bash
# List service accounts
gcloud iam service-accounts list --project=mycoolproject-prod

# Grant IAM role
gcloud projects add-iam-policy-binding mycoolproject-prod \
  --member="serviceAccount:name@project.iam.gserviceaccount.com" \
  --role="roles/role-name"

# Remove IAM role
gcloud projects remove-iam-policy-binding mycoolproject-prod \
  --member="serviceAccount:name@project.iam.gserviceaccount.com" \
  --role="roles/role-name"
```

---

## Workload Identity

```bash
# Get provider resource name
gcloud iam workload-identity-pools providers describe github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --format="value(name)"
```

---

## Docker

```bash
# Build image
docker build -t mycoolproject-app .

# Run locally
docker run --rm -p 8080:8080 \
  -e DATABASE_URL="postgres://..." \
  -e SECRET_KEY="test" \
  mycoolproject-app

# Tag for Artifact Registry
docker tag mycoolproject-app southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:latest

# Push
docker push southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:latest
```

---

## PlanetScale CLI

```bash
# Authenticate
pscale auth login

# Create database
pscale database create mycoolproject

# List databases
pscale database list

# Create branch
pscale branch create mycoolproject feature-branch

# List branches
pscale branch list mycoolproject

# Connect to branch (local development)
pscale connect mycoolproject development

# Delete branch
pscale branch delete mycoolproject feature-branch

# Get connection string
pscale connection-string mycoolproject main --fetch
```

---

## Django management commands

```bash
cd web

# Run migrations (in production via Cloud Run Job)
DJANGO_SETTINGS_MODULE=core.settings.prod uv run manage.py migrate

# Collectstatic (upload static files to GCS)
DJANGO_SETTINGS_MODULE=core.settings.prod uv run manage.py collectstatic --noinput

# Create superuser
DJANGO_SETTINGS_MODULE=core.settings.prod uv run manage.py createsuperuser --noinput

# Run tests
DJANGO_SETTINGS_MODULE=core.settings.test uv run manage.py test
```

---

## GitHub Actions workflow

The complete workflow is in `.github/workflows/deploy.yml`:

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

  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}
      - uses: google-github-actions/setup-gcloud@v2
      - name: Configure Docker
        run: gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev --quiet
      - name: Build image
        run: |
          docker build \
            -t ${{ env.IMAGE }}:${{ github.sha }} \
            -t ${{ env.IMAGE }}:latest \
            .
      - name: Push image
        run: docker push --all-tags ${{ env.IMAGE }}
      - name: Deploy to Cloud Run
        run: |
          gcloud run services update mycoolproject \
            --image=${{ env.IMAGE }}:${{ github.sha }} \
            --region=${{ env.REGION }}
      - name: Run migrations
        run: |
          gcloud run jobs execute migrate \
            --region=${{ env.REGION }} \
            --wait
```

---

## Health check

```bash
curl https://mycoolproject.com/health/
# Expected: {"status": "ok"}
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
- [09 — Secret Manager](09_secrets.md)
- [10 — Cloud Storage](10_storage.md)
- [11 — Service Accounts & IAM](11_iam.md)
- [12 — Cloud Run](12_cloud_run.md)
- [13 — Cloud Tasks & Scheduler](13_tasks.md)
- [14 — Dockerfile](14_dockerfile.md)
- [15 — First Deploy](15_first_deploy.md)
- [16 — Custom Domain & SSL](16_domain_ssl.md)
- [17 — Workload Identity Federation](17_wif.md)
- [18 — GitHub Actions CI/CD](18_github_actions.md)
- 19 — Quick Reference (Current chapter)