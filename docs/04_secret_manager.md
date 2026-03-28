---
description: "Securely store environment variables, passwords, and Django SECRET_KEYs using GCP Secret Manager."
image: assets/social-banner.png
---
# 04 — Secret Manager

← [Previous: 03 — Cloud SQL (PostgreSQL Database)](03_cloud_sql.md)

> ✅ **Practically free.** Free tier includes 6 secret versions and 10,000 access operations per month. This project stores ~11 secrets, which slightly exceeds the 6 free versions — cost is $0.06/version/month, so roughly **$0.30/month** total. Each container startup accesses secrets once; at low traffic this stays within the free access quota.

## What is Secret Manager?

Secret Manager is GCP's service for storing and accessing sensitive values: passwords, API keys, private keys. Instead of putting credentials in `.env` files on a server or hardcoding them, you store them here and the application fetches them at runtime.

## Why not just use environment variables?

You can set env vars directly on Cloud Run, but they appear in plain text in the GCP Console and deployment logs. Secret Manager encrypts values at rest, controls access via IAM, and keeps a version history so you can roll back a secret change.

## How does Django receive secrets?

In the Cloud Run deployment command, secrets are mapped to environment variables using `--set-secrets`. At container startup, Cloud Run fetches the secret values from Secret Manager and injects them as environment variables. Django reads them via `django-environ` the same way it reads a `.env` file.

For example, `--set-secrets=SECRET_KEY=DJANGO_SECRET_KEY:latest` makes the secret named `DJANGO_SECRET_KEY` available as the env var `SECRET_KEY` inside the container.

---

## Store all secrets

Run in your **local terminal**.

> **Platform note:** The examples below use `echo -n` (bash/Linux/Mac syntax). On **Windows PowerShell**, replace `echo -n "value" | gcloud secrets create ...` with:
> ```powershell
> "value" | gcloud secrets create SECRET_NAME --data-file=-
> ```
> Or use WSL2/Git Bash for consistency. **From this point on, all examples show Linux/Mac syntax.**

The `echo -n` pipe passes the value without a trailing newline:

```bash
# Each command below pipes a value via stdin (echo -n avoids a trailing newline that
# would corrupt the secret) and creates a named secret in Secret Manager.
# --data-file=- means "read value from stdin instead of a file".
# Result: all secrets visible at console.cloud.google.com/security/secret-manager

# PostgreSQL connection URL (built in chapter 03)
echo -n "postgresql://djangouser:<password>@/mycoolproject?host=/cloudsql/mycoolproject-prod:southamerica-east1:mycoolproject-db" \
  | gcloud secrets create DATABASE_URL --data-file=-

# Django secret key — used to sign cookies and CSRF tokens. Must be long and random.
# Generate with: python -c "import secrets; print(secrets.token_urlsafe(50))"
echo -n "<your-django-secret-key>" \
  | gcloud secrets create DJANGO_SECRET_KEY --data-file=-

# Google OAuth credentials — from Google Cloud Console → APIs & Services → Credentials
echo -n "<google-client-id>"     | gcloud secrets create GOOGLE_CLIENT_ID --data-file=-
echo -n "<google-client-secret>" | gcloud secrets create GOOGLE_CLIENT_SECRET --data-file=-

# SMTP credentials for transactional email (e.g. Brevo, SendGrid, or Gmail App Password)
echo -n "<smtp-host>"     | gcloud secrets create EMAIL_HOST --data-file=-
echo -n "587"             | gcloud secrets create EMAIL_PORT --data-file=-
echo -n "<smtp-user>"     | gcloud secrets create EMAIL_HOST_USER --data-file=-
echo -n "<smtp-password>" | gcloud secrets create EMAIL_HOST_PASSWORD --data-file=-

# Didit KYC — credentials for the identity verification service
echo -n "<didit-api-key>"        | gcloud secrets create DIDIT_API_KEY --data-file=-
echo -n "<didit-workflow-id>"    | gcloud secrets create DIDIT_WORKFLOW_ID --data-file=-
echo -n "<didit-webhook-secret>" | gcloud secrets create DIDIT_WEBHOOK_SECRET --data-file=-
```

## Update a secret

Each update creates a new version. The `latest` alias always points to the newest:

```bash
# Adds a new version to an existing secret. The previous version is kept (not deleted).
# Cloud Run picks up the new value on next container restart / new deploy.
echo -n "new-value" | gcloud secrets versions add SECRET_NAME --data-file=-
```

The running Cloud Run container won't pick up the new value until it restarts. Trigger a new deploy to apply a secret rotation.

## Verify stored secrets

```bash
# Lists all secret names in the project (values are not shown).
gcloud secrets list

# Lists all stored versions of a secret — useful to confirm an update landed.
gcloud secrets versions list DATABASE_URL

# Prints a secret's value to the terminal — use with care, avoid in shared sessions.
gcloud secrets versions access latest --secret=DATABASE_URL
```

---

## 📖 Navigation

- [01 — GCP Project Setup](01_gcp_setup.md)
- [02 — Artifact Registry](02_artifact_registry.md)
- [03 — Cloud SQL (PostgreSQL Database)](03_cloud_sql.md)
- **04 — Secret Manager** (current chapter)
- [05 — Cloud Storage (Media & Static Files)](05_cloud_storage.md)
- [06 — Dockerfile](06_dockerfile.md)
- [07 — First Deploy](07_first_deploy.md)
- [08 — Custom Domain & SSL](08_domain_ssl.md)
- [09 — Workload Identity Federation (Keyless GitHub Actions Auth)](09_workload_identity.md)
- [10 — GitHub Actions CI/CD Pipeline](10_github_actions.md)
- [11 — Quick Reference](11_quick_reference.md)
