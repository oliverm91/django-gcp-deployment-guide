---
description: "Manually deploy your Django app to Cloud Run for the first time to verify the entire infrastructure works."
image: assets/social-banner.png
---

# 15 — First Deploy

← [Previous: 13 — Dockerfile](14_dockerfile.md)

This chapter walks through deploying to Cloud Run manually for the first time. After this, GitHub Actions will handle it automatically.

---

## Prerequisites

Before deploying, make sure you have:

1. **All Terraform resources created** (chapters 05-13)
2. **Secrets set in Secret Manager** (chapter 09)
3. **Docker image built and pushed** to Artifact Registry
4. **PlanetScale database created** (chapter 04)
5. **Domain pointed to Cloud Run** (or skip this for now — use the `.run.app` URL)

---

## Step 1: Authenticate Docker to Artifact Registry

```bash
gcloud auth configure-docker southamerica-east1-docker.pkg.dev
```

---

## Step 2: Build and push the Docker image

```bash
# Set the image URL
IMAGE="southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app"

# Build with two tags
docker build -t $IMAGE:latest -t $IMAGE:$(git rev-parse --short HEAD) .

# Push both tags
docker push --all-tags $IMAGE
```

---

## Step 3: Set secret values (if not done yet)

```bash
# Database URL (from PlanetScale dashboard)
echo -n "postgres://user:password@aws.connect.psdb.cloud/mycoolproject?sslmode=require" \
  | gcloud secrets versions add DATABASE_URL --data-file=-

# Django secret key
python -c "import secrets; print(secrets.token_urlsafe(50))"
echo -n "<generated-key>" | gcloud secrets versions add DJANGO_SECRET_KEY --data-file=-

# ALLOWED_HOSTS
echo -n "mycoolproject.com,www.mycoolproject.com" | gcloud secrets versions add ALLOWED_HOSTS --data-file=-
```

---

## Step 4: Verify Cloud Run is deployed

```bash
# Get the service URL
gcloud run services describe mycoolproject --region=southamerica-east1 --format="value(status.url)"

# Test the health endpoint
curl https://<url>/health/
```

Should return `{"status": "ok"}`.

---

## Step 5: Run migrations on PlanetScale

Since we can't use `gcloud sql` (no Cloud SQL), we use a Cloud Run Job to run migrations:

```bash
# Create a temporary job to run migrations
gcloud run jobs create migrate \
  --image=$IMAGE:latest \
  --region=southamerica-east1 \
  --service-account=mycoolproject-worker@mycoolproject-prod.iam.gserviceaccount.com \
  --set-env-vars=DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest \
  --command="uv,run,manage.py,migrate"

# Run it
gcloud run jobs execute migrate --region=southamerica-east1 --wait
```

---

## Step 6: Collectstatic

Upload static files to Cloud Storage:

```bash
docker run --rm \
  -e DATABASE_URL=DATABASE_URL:latest \
  -e SECRET_KEY=DJANGO_SECRET_KEY:latest \
  -e DJANGO_SETTINGS_MODULE=core.settings.prod \
  -e GS_PROJECT_ID=mycoolproject-prod \
  $IMAGE:latest \
  uv run manage.py collectstatic --noinput
```

Wait, this won't work — it needs access to Secret Manager. Instead, use a Cloud Run Job:

```bash
# Create job for collectstatic
gcloud run jobs create collectstatic \
  --image=$IMAGE:latest \
  --region=southamerica-east1 \
  --service-account=mycoolproject-worker@mycoolproject-prod.iam.gserviceaccount.com \
  --set-secrets=DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest,GS_PROJECT_ID=mycoolproject-prod:latest \
  --command="uv,run,manage.py,collectstatic,--noinput"

# Run it
gcloud run jobs execute collectstatic --region=southamerica-east1 --wait
```

---

## Verify everything works

```bash
# Test the site
curl https://mycoolproject-<hash>-uc.a.run.app/

# Check logs
gcloud run services logs tail mycoolproject --region=southamerica-east1
```

---

## If something goes wrong

### Check the logs

```bash
gcloud run services logs tail mycoolproject --region=southamerica-east1
```

### Check Cloud Run revisions

```bash
gcloud run revisions list --service=mycoolproject --region=southamerica-east1
```

### Roll back to a previous image

```bash
# Get the previous image tag (from git history or Artifact Registry)
docker pull southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:<previous-sha>

# Update Cloud Run
gcloud run services update mycoolproject \
  --image=southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:<previous-sha> \
  --region=southamerica-east1
```

---

## What's next

Now that the app is deployed, we need:
- Custom domain + SSL (chapter 16)
- Workload Identity Federation for GitHub Actions (chapter 17)
- GitHub Actions CI/CD pipeline (chapter 18)

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
- [09 — Cloud Storage](10_storage.md)
- [10 — Service Accounts & IAM](11_iam.md)
- [11 — Cloud Run](12_cloud_run.md)
- [12 — Cloud Tasks & Scheduler](13_tasks.md)
- [13 — Dockerfile](14_dockerfile.md)
- 14 — First Deploy (Current chapter)
- [15 — Custom Domain & SSL](16_domain_ssl.md)
- [16 — Workload Identity Federation](17_wif.md)
- [17 — GitHub Actions CI/CD](18_github_actions.md)
- [18 — Quick Reference](19_quick_reference.md)