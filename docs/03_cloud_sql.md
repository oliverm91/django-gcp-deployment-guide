---
description: "Provision and securely connect a managed PostgreSQL database using Cloud SQL for your production Django application."
image: assets/social-banner.png

---
# 03 — Cloud SQL (PostgreSQL Database)

← [Previous: 02 — Artifact Registry](02_artifact_registry.md)

> 💰 **Costs money — set this up last, right before go-live.**
>
> Cloud SQL has **no free tier**. The smallest instance (`db-f1-micro`) costs approximately **$7–10/month** and the clock starts the moment you create it, whether the app is live or not. Pausing the instance stops compute billing but still charges for storage.
>
> **Recommended:** complete all other chapters first. Create the Cloud SQL instance only when you're ready to deploy and go live, to minimise idle spend.

## What is Cloud SQL?

Cloud SQL is Google's managed PostgreSQL service. "Managed" means Google handles the server, OS patches, backups, and high availability — you just connect to it and use it like a regular PostgreSQL database. You never SSH into the database server.

## How does Cloud Run connect to it?

Cloud Run connects to Cloud SQL through a **Unix socket** — not over the internet, not over a public IP. The Cloud SQL Auth Proxy runs as a sidecar inside Cloud Run and exposes the database at `/cloudsql/<instance-connection-name>`. The connection string uses this socket path:

```
postgresql://user:password@/dbname?host=/cloudsql/mycoolproject-prod:southamerica-east1:mycoolproject-db
```

This means the database is never publicly accessible — no firewall rules, no VPC setup needed.

---

## Create the instance

Run in your **local terminal**:

```bash
# Creates a managed PostgreSQL 15 instance. Takes 3–5 minutes.
# ⚠️  Billing starts immediately after creation (~$7/mo). Only run this when ready to go live.
# Result: visible at console.cloud.google.com/sql/instances
gcloud sql instances create mycoolproject-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=southamerica-east1 \
  --storage-auto-increase \
  --backup-start-time=03:00 \
  --retained-backups-count=7
```

Options explained:

- `--tier=db-f1-micro` — smallest instance, 0.6 GB RAM (~$7/mo). Sufficient for early traffic.
- `--storage-auto-increase` — disk grows automatically as data grows.
- `--backup-start-time=03:00` — daily automatic backup at 3 AM UTC.
- `--retained-backups-count=7` — keeps 7 days of backups for point-in-time recovery.

This takes 3–5 minutes to provision.

---

## Create the database and user

```bash
# Creates a database named "mycoolproject" inside the instance.
# The instance is the server; the database is a logical namespace inside it.
# Result: visible at console.cloud.google.com/sql/instances/mycoolproject-db/databases
gcloud sql databases create mycoolproject --instance=mycoolproject-db

# Creates a dedicated PostgreSQL user for the Django app.
# Never use the default postgres superuser in production — it has unrestricted access.
# Generate a strong password with: openssl rand -base64 32
# You'll store this password in Secret Manager (chapter 04) — no need to memorise it.
gcloud sql users create djangouser \
  --instance=mycoolproject-db \
  --password=<strong-password>
```

Use a strong random password here (e.g. `openssl rand -base64 32`). You'll store it in Secret Manager in the next chapter — you won't need to remember it.

---

## The connection string

The `DATABASE_URL` secret you'll create in Secret Manager uses this format:

```
postgresql://djangouser:<password>@/mycoolproject?host=/cloudsql/mycoolproject-prod:southamerica-east1:mycoolproject-db
```

Breaking it down:

- `djangouser` — the DB user created above
- `<password>` — the password set above
- `/mycoolproject` — the database name
- `host=/cloudsql/...` — the Unix socket path to Cloud SQL (no public IP)

Django reads this via `DATABASE_URL` in `prod.py`:

```python
# web/core/settings/base.py
DATABASES = {
    'default': env.db('DATABASE_URL', default='...')
}
```

`env.db()` parses the URL and builds Django's `DATABASES` dict automatically using `django-environ`.

---

## Migrations

Migrations are Django's way of keeping the database schema in sync with your models. Every time you add a field or create a model, Django generates a migration file. These must be applied to the database before the new code runs.

In this setup, migrations run as a **Cloud Run Job** — a one-off container execution that runs `manage.py migrate` against the production database before each deploy. See [chapter 07](07_first_deploy.md) for setup.

---

## 📖 Navigation

- [01 — GCP Project Setup](01_gcp_setup.md)
- [02 — Artifact Registry](02_artifact_registry.md)
- 03 — Cloud SQL (PostgreSQL Database) (Current chapter)
- [04 — Secret Manager](04_secret_manager.md)
- [05 — Cloud Storage (Media & Static Files)](05_cloud_storage.md)
- [06 — Dockerfile](06_dockerfile.md)
- [07 — First Deploy](07_first_deploy.md)
- [08 — Custom Domain & SSL](08_domain_ssl.md)
- [09 — Workload Identity Federation (Keyless GitHub Actions Auth)](09_workload_identity.md)
- [10 — GitHub Actions CI/CD Pipeline](10_github_actions.md)
- [11 — Quick Reference](11_quick_reference.md)
- [12 — Bonus: Custom Email (@domain.cl)](12_custom_email.md)
