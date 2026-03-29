---
description: "Manually deploy your Dockerized Django app to Cloud Run for the first time to verify end-to-end functionality."
image: assets/social-banner.png

---
# 07 — First Deploy

← [Previous: 06 — Dockerfile](06_dockerfile.md)

> ✅ **Cloud Run is free at low traffic.** Free tier: 2 million requests/month, 360,000 GB-seconds of CPU, 180,000 GB-seconds of memory. With `--min-instances=0`, the service scales to zero when idle — no requests means no cost. A typical small marketplace stays within the free tier for months.

This chapter deploys MyCoolProject to Cloud Run for the first time. This is done manually from your local machine. After this, GitHub Actions takes over for all subsequent deploys.

---

## Runtime Architecture

Before we actually execute the deployment, let's look at exactly what we are building. The final production container acts as the brain of the operation, communicating dynamically with our configured suite of GCP services:

![Runtime Architecture Component Map](assets/diagram-runtime.svg)

---

## Build and push the image

> The `mycoolproject-prod` project and `mycoolproject-repo` registry must exist (created in [chapters 01](01_gcp_setup.md) and [02](02_artifact_registry.md)). This command creates the `app` image inside that registry.

Run from the local repo root:

```bash
IMAGE="southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/app"

# Configures Docker to use gcloud credentials for this registry. One-time per machine.
# After this, docker push/pull to this registry works without a separate login step.
gcloud auth configure-docker southamerica-east1-docker.pkg.dev

# Builds the Docker image from the Dockerfile at the repo root and tags it with the
# full Artifact Registry path so docker push knows where to send it.
docker build -t $IMAGE:latest .

# Uploads the image to Artifact Registry. Cloud Run will pull it from here on deploy.
# Result: visible at console.cloud.google.com/artifacts/docker/mycoolproject-prod
docker push $IMAGE:latest
```

---

## Deploy to Cloud Run

### What is Cloud Run?

Cloud Run is a serverless container platform. You give it a Docker image and it:

- Starts container instances to handle incoming requests
- Scales to zero when there's no traffic (no cost when idle)
- Scales up automatically under load
- Provides a public HTTPS URL automatically
- Manages SSL certificates automatically

You never provision servers, install OS patches, or configure load balancers.

```bash
# Deploys the image to Cloud Run for the first time, creating a new service named "mycoolproject".
# Subsequent deploys only need: gcloud run deploy mycoolproject --image=... --region=...
# (All other flags are remembered by the service after the first deploy.)
# Result: prints the service URL when complete — visit it to confirm the site is live.
# Also visible at console.cloud.google.com/run/detail/southamerica-east1/mycoolproject
gcloud run deploy mycoolproject \
  --image=$IMAGE:latest \
  --region=southamerica-east1 \
  --platform=managed \
  --allow-unauthenticated \
  --service-account=mycoolproject-run-sa@mycoolproject-prod.iam.gserviceaccount.com \
  --add-cloudsql-instances=mycoolproject-prod:southamerica-east1:mycoolproject-db \
  --set-secrets=DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest,GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest,EMAIL_HOST=EMAIL_HOST:latest,EMAIL_PORT=EMAIL_PORT:latest,EMAIL_HOST_USER=EMAIL_HOST_USER:latest,EMAIL_HOST_PASSWORD=EMAIL_HOST_PASSWORD:latest,DIDIT_API_KEY=DIDIT_API_KEY:latest,DIDIT_WORKFLOW_ID=DIDIT_WORKFLOW_ID:latest,DIDIT_WEBHOOK_SECRET=DIDIT_WEBHOOK_SECRET:latest \
  --set-env-vars=ALLOWED_HOSTS=mycoolproject.cl \
  --min-instances=0 \
  --max-instances=5 \
  --memory=512Mi \
  --cpu=1
```

Flags explained:

| Flag | Meaning |
|---|---|
| `--allow-unauthenticated` | Public internet can access the service (required for a public website) |
| `--service-account` | The container runs as `mycoolproject-run-sa` — gets its GCS/SQL/Secret permissions automatically |
| `--add-cloudsql-instances` | Attaches the Cloud SQL proxy — enables the Unix socket connection to the database |
| `--set-secrets` | Fetches these Secret Manager secrets and injects them as environment variables |
| `--set-env-vars` | Plain (non-secret) environment variables |
| `--min-instances=0` | **Scale to zero when idle.** No cost when traffic stops. Cold start: first request after idle takes ~1–2 s (Container startup + DB connection). Good for low-traffic sites. **vs** `--min-instances=1` keeps one instance always warm: immediate response, but costs ~$5–10/month always (even with zero traffic). Choose 0 for development/low traffic; choose 1 if sub-second response critical. |
| `--max-instances=5` | Hard cap on concurrent container instances |
| `--memory=512Mi` | RAM per container instance |

After deploy, `gcloud` prints the service URL: `https://mycoolproject-<hash>-uc.a.run.app`

---

## Run database migrations

### What is a Cloud Run Job?

A Cloud Run Job is a one-off container execution — it runs to completion and exits, unlike a Cloud Run Service which stays running to handle HTTP traffic. Jobs are ideal for `manage.py migrate` — you want to run migrations exactly once per deploy, not on every request.

Create the migrate job (one-time):

```bash
# Creates a Cloud Run Job named "migrate". A Job is a one-off container execution
# (runs to completion and exits), unlike a Service which handles ongoing HTTP traffic.
# This job runs `manage.py migrate` against the production database.
# Only needs to be created once — GitHub Actions updates its image on every deploy.
# Result: visible at console.cloud.google.com/run/jobs
gcloud run jobs create migrate \
  --image=$IMAGE:latest \
  --region=southamerica-east1 \
  --service-account=mycoolproject-run-sa@mycoolproject-prod.iam.gserviceaccount.com \
  --add-cloudsql-instances=mycoolproject-prod:southamerica-east1:mycoolproject-db \
  --set-secrets=DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest \
  --command="uv,run,manage.py,migrate"
```

Execute it and wait for it to finish:

```bash
# Runs the migrate job and waits for it to finish before returning.
# --wait blocks your terminal and streams the output — you'll see Django's migration log.
# If migrations fail, the command exits non-zero and prints the error.
# Result: execution log visible at console.cloud.google.com/run/jobs/details/southamerica-east1/migrate
gcloud run jobs execute migrate --region=southamerica-east1 --wait
```

`--wait` blocks your terminal until the job completes and prints the output. If migrations fail, the job exits non-zero and you'll see the error.

In subsequent deploys, GitHub Actions updates the job's image and re-runs it automatically before deploying the new service revision.

---

## Verify the deploy

```bash
# Prints the public URL of the deployed service.
# Paste it in your browser to confirm the site is reachable.
gcloud run services describe mycoolproject \

  --region=southamerica-east1 \
  --format="value(status.url)"

# Streams live logs from the running containers to your terminal (Ctrl+C to stop).
# Useful to watch requests come in and spot errors right after deploy.
# Logs are also stored permanently at console.cloud.google.com/logs
gcloud run services logs tail mycoolproject --region=southamerica-east1
```

Visit `<url>/health/` — should return `{"status": "ok"}`.

---

## Django superuser (one-time)

You can't run `manage.py createsuperuser` interactively in Cloud Run. Instead, use the Cloud Run Jobs approach:

```bash
# Creates a one-off job to run createsuperuser non-interactively.
# --noinput reads email/password from env vars instead of prompting.
# Use a temporary password here — change it immediately after first login at /admin/.
gcloud run jobs create createsuperuser \

  --image=$IMAGE:latest \
  --region=southamerica-east1 \
  --service-account=mycoolproject-run-sa@mycoolproject-prod.iam.gserviceaccount.com \
  --add-cloudsql-instances=mycoolproject-prod:southamerica-east1:mycoolproject-db \
  --set-secrets=DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest \
  --set-env-vars=DJANGO_SUPERUSER_EMAIL=admin@mycoolproject.cl,DJANGO_SUPERUSER_PASSWORD=<temp-password> \
  --command="uv,run,manage.py,createsuperuser,--noinput"

# Executes the job and waits. On success, log in at <service-url>/admin/ with the temp password.
gcloud run jobs execute createsuperuser --region=southamerica-east1 --wait
```

Change the password immediately after first login.

---

## 📖 Navigation

- [01 — GCP Project Setup](01_gcp_setup.md)
- [02 — Artifact Registry](02_artifact_registry.md)
- [03 — Cloud SQL (PostgreSQL Database)](03_cloud_sql.md)
- [04 — Secret Manager](04_secret_manager.md)
- [05 — Cloud Storage (Media & Static Files)](05_cloud_storage.md)
- [06 — Dockerfile](06_dockerfile.md)
- 07 — First Deploy (Current chapter)
- [08 — Custom Domain & SSL](08_domain_ssl.md)
- [09 — Workload Identity Federation (Keyless GitHub Actions Auth)](09_workload_identity.md)
- [10 — GitHub Actions CI/CD Pipeline](10_github_actions.md)
- [11 — Quick Reference](11_quick_reference.md)
- [12 — Bonus: Custom Email (@domain.cl)](12_custom_email.md)
