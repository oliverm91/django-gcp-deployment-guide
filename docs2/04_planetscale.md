---
description: "Understand what PlanetScale is, how its serverless Postgres works, branching workflow, and how to connect from Django."
image: assets/social-banner.png
---

# 04 — PlanetScale Database Explained

← [Previous: 03 — Cloud Services Explained](03_cloud_services.md)

PlanetScale is the managed Postgres database we'll use instead of GCP's Cloud SQL. This chapter explains how it works, why we chose it, and the key concepts you need to understand before setting it up.

---

## What is PlanetScale?

PlanetScale is a **managed Postgres database**. It's serverless, which means:

- No server management (no patching, no backups to manage, no scaling to worry about)
- You connect to a database URL — PlanetScale handles everything else
- It scales automatically to handle traffic spikes

### Compared to Cloud SQL

| Feature | Cloud SQL | PlanetScale |
|---|---|---|
| Server management | You manage it | Fully managed |
| Scaling | Manual (choose instance size) | Automatic (serverless) |
| Branching | No | Yes (like Git branches) |
| Free tier | No | No (paid plans start at $5/mo) |
| Cost | ~$7–10/month (starts immediately) | $5/mo for single-node Postgres |

---

## Key concepts

### Database vs Branch

In PlanetScale:

- **Database** — the production database where your data lives
- **Branch** — a copy of the database that you can develop on, test on, and merge back

This is like Git:
- `main` branch = production database
- Feature branches = development branches
- Merge = schema changes get applied to production

### Schema changes as deploys

PlanetScale's branching workflow works great with GitHub Actions:

1. Create a branch for your feature
2. Make schema changes (add columns, etc.)
3. Open a PR — PlanetScale can run a "schema review" to show what would change
4. Merge to main — PlanetScale applies the changes with zero downtime

PlanetScale supports **non-blocking schema changes** — altering tables without locking them.

### Connection string

PlanetScale gives you a connection string (like `postgres://user:password@aws.connect.psdb.cloud/db?sslmode=require`). You store this in Secret Manager and use it in Django's `DATABASE_URL`.

---

## Why PlanetScale for Django?

### Pros

1. **Serverless** — no database server to manage
2. **Branching** — perfect for testing migrations before they go live
3. **No maintenance** — no backups to run, no patches to apply
4. **Affordable** — single-node Postgres starts at $5/mo
5. **Django-compatible** — works with standard Postgres drivers

### Cons

1. **No superuser access** — you can't SSH in or run `psql` directly (it's a read-only connection)
2. **Some Postgres features limited** — not 100% feature parity with standard Postgres (no foreign keys, some locking behaviors differ)
3. **Cost** — production database costs money

### Compatibility notes for Django

PlanetScale is compatible with Django's ORM, but there are some caveats:

1. **No foreign key constraints** — PlanetScale doesn't support foreign keys due to its distributed nature. You'll need to use `db_constraint=False` on ForeignKey fields or handle referential integrity at the application level.

2. **No `SELECT FOR UPDATE`** — some locking queries aren't supported.

3. **Migrations** — Django migrations work fine, but you can't use `migrate` to create the initial database (PlanetScale creates it for you via their CLI).

For most Django apps, these limitations are manageable. If you need full Postgres features, consider using Cloud SQL instead.

---

## PlanetScale CLI

PlanetScale has a CLI (`pscale`) for managing databases and branches. You'll need it to:

- Create the initial database
- Create branches
- Run migrations against a branch
- Connect to a branch locally

Install it:

```bash
# macOS
brew install planetscale/tap/pscale

# Linux
curl -fsSL https://github.com/planetscale/cli/releases/download/v0.219.0/pscale_0.219.0_linux_amd64.tar.gz | tar -xz
sudo mv pscale /usr/local/bin/

# Verify
pscale version
```

Authenticate:

```bash
pscale auth login
```

---

## Creating the database

### Via the PlanetScale dashboard

1. Go to [app.planetscale.com](https://app.planetscale.com)
2. Create an account
3. Create a new database (call it `mycoolproject`)
4. Note the connection string

### Via the CLI

```bash
pscale database create mycoolproject
```

---

## Database branches

### Development vs Production

- **Development branch** — the default branch when you create a database. Use this for local development and testing migrations.

- **Production branch** — the production database. Only merge schema changes here after testing on the development branch.

### Creating a branch

```bash
# Create a branch for working on a feature
pscale branch create mycoolproject feature-add-users

# List branches
pscale branch list mycoolproject

# Delete a branch when done
pscale branch delete mycoolproject feature-add-users
```

### Connecting to a branch

Each branch has its own connection string. Use the development branch for local development, and only connect to production when deploying.

```bash
# Get connection string for a branch (for local development)
pscale connect mycoolproject development
```

This opens a local proxy so you can connect to the PlanetScale branch as if it were a local database.

---

## Connecting from Django

### The connection string format

PlanetScale connection strings look like:

```
postgres://user:password@aws.connect.psdb.cloud/db?sslmode=require
```

### Store in Secret Manager

Store this in Secret Manager using the gcloud CLI:

```bash
echo -n "postgres://user:password@aws.connect.psdb.cloud/mycoolproject?sslmode=require" \
  | gcloud secrets create DATABASE_URL --data-file=-
```

### Django settings

Django reads this via `django-environ`:

```python
# web/core/settings/prod.py
import environ

env = environ.Env()

DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}
```

The `DATABASE_URL` environment variable is injected from Secret Manager at container runtime. No special PlanetScale configuration needed — it works with standard Postgres drivers.

---

## SSL/TLS requirement

PlanetScale requires SSL connections. The `?sslmode=require` in the connection string handles this. Most Postgres drivers support this out of the box.

If you see SSL errors, check that your connection string includes `sslmode=require`.

---

## PlanetScale vs Cloud SQL

Here's the decision matrix:

| Scenario | Use PlanetScale | Use Cloud SQL |
|---|---|---|
| Starting out / learning | ✓ (paid plans from $5/mo) | ✗ (no free tier) |
| Simple Django app | ✓ | ✓ |
| Need foreign keys | ✗ | ✓ |
| Need full Postgres features | ✗ | ✓ |
| Want branching workflow | ✓ | ✗ |
| Serverless preferred | ✓ | ✗ |
| Tight budget | ✗ (paid required) | ✓ (~$7/mo) |

For this guide, we use PlanetScale because of the branching workflow which pairs well with GitHub Actions, and serverless scaling.

---

## Summary: what we've done

- Created a PlanetScale database (via dashboard or CLI)
- Stored the connection string in Secret Manager
- Configured Django to read `DATABASE_URL` from the environment

The Terraform infrastructure (Artifact Registry, Cloud Run, IAM, other secrets) is set up in the next chapters.

---

## Navigation



- [01 — Introduction: What We're Building](01_introduction.md)
- [02 — Terraform Overview](02_terraform_overview.md)
- [03 — Cloud Services Explained](03_cloud_services.md)
- 04 — PlanetScale Database Explained (Current chapter)
- [05 — Project Setup & Terraform State](05_project_setup.md)
- [06 — GCP Project & APIs](06_gcp_project.md)
- [07 — Artifact Registry](07_artifact_registry.md)
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
- [19 — Quick Reference](19_quick_reference.md)
