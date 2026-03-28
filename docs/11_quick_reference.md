---
description: "A quick reference guide and cheat sheet for every gcloud and deployment command used throughout the Cloud Run Django guide."
---
# 11 — Quick Reference

← [Previous: 10 — GitHub Actions CI/CD Pipeline](10_github_actions.md)

## Deploy manually (same steps as GitHub Actions)

```bash
IMAGE="southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/app"

docker build -t $IMAGE:latest .    # Build image from Dockerfile at repo root
docker push $IMAGE:latest          # Upload image to Artifact Registry

gcloud run jobs update migrate --image=$IMAGE:latest --region=southamerica-east1  # Point migrate job at new image
gcloud run jobs execute migrate --region=southamerica-east1 --wait                # Run migrations, wait for completion

gcloud run deploy mycoolproject --image=$IMAGE:latest --region=southamerica-east1  # Deploy new image to Cloud Run
```

## Run migrations without rebuilding

```bash
gcloud run jobs execute migrate --region=southamerica-east1 --wait
```

## View live logs

```bash
# Streams live logs to terminal — useful right after a deploy (Ctrl+C to stop)
gcloud run services logs tail mycoolproject --region=southamerica-east1

# Fetches the last 50 error-level log entries from Cloud Logging
gcloud logging read \
  'resource.type="cloud_run_revision" AND severity>=ERROR' \
  --project=mycoolproject-prod --limit=50
```

## Secrets

```bash
# Add a new secret
echo -n "value" | gcloud secrets create SECRET_NAME --data-file=-

# Update an existing secret
echo -n "new-value" | gcloud secrets versions add SECRET_NAME --data-file=-

# Read a secret (careful — prints to terminal)
gcloud secrets versions access latest --secret=SECRET_NAME

# List all secrets
gcloud secrets list
```

## Cloud Run

```bash
# Shows service details, URL, current revision, and traffic split
gcloud run services describe mycoolproject --region=southamerica-east1

# Lists revisions (most recent first) — use to find revision name for rollback
gcloud run revisions list --service=mycoolproject --region=southamerica-east1

# Instantly shifts 100% of traffic to a previous revision (instant rollback)
gcloud run services update-traffic mycoolproject \
  --region=southamerica-east1 \
  --to-revisions=mycoolproject-<revision-name>=100

# Updates an env var on the live service without rebuilding the image
gcloud run services update mycoolproject \
  --region=southamerica-east1 \
  --update-env-vars=ALLOWED_HOSTS="mycoolproject.cl,www.mycoolproject.cl"
```

## Cloud SQL

```bash
# Prints the instance state (RUNNABLE = healthy, SUSPENDED = paused to save cost)
gcloud sql instances describe mycoolproject-db --format="value(state)"

# Opens an interactive psql session to the production database via the Cloud SQL proxy
# Use with care — this is direct access to prod data
gcloud sql connect mycoolproject-db --user=djangouser --database=mycoolproject
```

## Django management commands via Cloud Run Job

For any one-off `manage.py` command in production, create or reuse a Cloud Run Job:

```bash
# Example: run a custom management command
gcloud run jobs create my-command \
  --image=southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/app:latest \
  --region=southamerica-east1 \
  --service-account=mycoolproject-run-sa@mycoolproject-prod.iam.gserviceaccount.com \
  --add-cloudsql-instances=mycoolproject-prod:southamerica-east1:mycoolproject-db \
  --set-secrets=DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest \
  --command="uv,run,manage.py,your_command"

gcloud run jobs execute my-command --region=southamerica-east1 --wait
```

## Static files

```bash
# Re-upload static files to GCS after CSS/JS/icon changes
cd web
DJANGO_SETTINGS_MODULE=core.settings.prod uv run manage.py collectstatic --noinput
```

## Health check

```bash
curl https://mycoolproject.cl/health/
# Expected: {"status": "ok"}
```

---

## 📖 Navigation

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
- **11 — Quick Reference** (current chapter)
