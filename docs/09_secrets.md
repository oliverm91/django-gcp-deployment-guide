---
description: "Store credentials, API keys, and connection strings in GCP Secret Manager using Terraform."
image: assets/social-banner.png
---

# 09 — Secret Manager

← [Previous: 07 — Artifact Registry](07_artifact_registry.md)

Secret Manager stores sensitive values like passwords, API keys, and connection strings. In this chapter, we'll create secrets with Terraform and store the actual values via the CLI.

---

## Why Secret Manager?

Before Secret Manager, teams would put secrets in:
- Environment variables (visible in logs, plain text in console)
- `.env` files (committed to git accidentally, leaked)
- Code (worst — visible in source history)

Secret Manager provides:
- Encryption at rest
- Version history
- IAM access control
- Runtime injection into Cloud Run

### Terraform vs. manual: who does what?

Terraform defines the **structure** — what secrets exist, their names, replication settings. The **actual values** (passwords, API keys, connection strings) are set separately and never stored in Terraform state.

This is intentional: Terraform state files are stored in version control or cloud storage, and storing secret values in state would be a security risk. Instead:

- **Terraform** creates the secret container
- **You** set the value via CLI (or CI/CD pipeline)
- **Cloud Run** reads the value at runtime

---

## Create secrets with Terraform

Add to `infrastructure/main.tf`:

```hcl
# Secret Manager secrets
resource "google_secret_manager_secret" "database_url" {
  secret_id = "DATABASE_URL"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "django_secret_key" {
  secret_id = "DJANGO_SECRET_KEY"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "google_client_id" {
  secret_id = "GOOGLE_CLIENT_ID"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "google_client_secret" {
  secret_id = "GOOGLE_CLIENT_SECRET"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "email_host" {
  secret_id = "EMAIL_HOST"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "email_port" {
  secret_id = "EMAIL_PORT"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "email_host_user" {
  secret_id = "EMAIL_HOST_USER"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "email_host_password" {
  secret_id = "EMAIL_HOST_PASSWORD"
  replication {
    auto {}
  }
}
```

Run `terraform apply` to create the secret structure.

---

## Set secret values (via CLI, not Terraform)

Terraform can store the *secret structure* but **not** the actual values — secrets are set at runtime, not baked into the state. Use the `gcloud` CLI to set each secret:

```bash
# Database URL (from PlanetScale)
echo -n "postgres://user:password@aws.connect.psdb.cloud/mycoolproject?sslmode=require" \
  | gcloud secrets versions add DATABASE_URL --data-file=-

# Django secret key (generate a random one)
python -c "import secrets; print(secrets.token_urlsafe(50))"
# Copy the output and use it:
echo -n "<your-generated-secret-key>" \
  | gcloud secrets versions add DJANGO_SECRET_KEY --data-file=-

# Google OAuth credentials (from Google Cloud Console)
echo -n "<your-google-client-id>" \
  | gcloud secrets versions add GOOGLE_CLIENT_ID --data-file=-

echo -n "<your-google-client-secret>" \
  | gcloud secrets versions add GOOGLE_CLIENT_SECRET --data-file=-

# Email (SMTP credentials from your email provider)
echo -n "smtp.sendgrid.net" \
  | gcloud secrets versions add EMAIL_HOST --data-file=-

echo -n "587" \
  | gcloud secrets versions add EMAIL_PORT --data-file=-

echo -n "<your-smtp-username>" \
  | gcloud secrets versions add EMAIL_HOST_USER --data-file=-

echo -n "<your-smtp-password>" \
  | gcloud secrets versions add EMAIL_HOST_PASSWORD --data-file=-
```

### Generate a Django secret key

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

This generates a cryptographically secure random string suitable for Django's `SECRET_KEY`.

---

## How Cloud Run uses secrets

When we deploy to Cloud Run later, we map secrets to environment variables:

```bash
--set-secrets=DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest
```

This tells Cloud Run: "Fetch the latest version of `DATABASE_URL` from Secret Manager and inject it as the environment variable `DATABASE_URL` inside the container."

---

## IAM: Allow Cloud Run to read secrets

We need to grant the service account permission to read secrets. We'll create the service account in the next chapter, but here's the Terraform:

```hcl
# Allow Cloud Run service account to read all our secrets
resource "google_secret_manager_secret_iam_binding" "run_secret_accessor" {
  secret_id = google_secret_manager_secret.database_url.secret_id
  role     = "roles/secretmanager.secretAccessor"
  members  = ["serviceAccount:${google_service_account.run.email}"]
}

# Repeat for other secrets, or use a project-level policy
resource "google_project_iam_member" "run_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.run.email}"
}
```

Using `google_project_iam_member` with `roles/secretmanager.secretAccessor` at the project level is easier — it grants access to all secrets in the project.

---

## Verify secrets exist

```bash
gcloud secrets list
```

You should see all the secrets we created.

---

## Update a secret (for rotation)

```bash
echo -n "new-value" | gcloud secrets versions add SECRET_NAME --data-file=-
```

The `latest` tag always points to the newest version. Cloud Run picks up the new value on next container restart or new deploy.

---

## Navigation



- [01 — Introduction: What We're Building](01_introduction.md)
- [02 — Terraform Overview](02_terraform_overview.md)
- [03 — Cloud Services Explained](03_cloud_services.md)
- [04 — PlanetScale Database Explained](04_planetscale.md)
- [05 — Project Setup & Terraform State](05_project_setup.md)
- [06 — GCP Project & APIs](06_gcp_project.md)
- [07 — Artifact Registry](07_artifact_registry.md)
- 08 — Secrets Management (Current chapter)
- [09 — Cloud Storage](10_storage.md)
- [10 — Service Accounts & IAM](11_iam.md)
- [11 — Cloud Run](12_cloud_run.md)
- [12 — Cloud Tasks & Scheduler](13_tasks.md)
- [13 — Dockerfile](14_dockerfile.md)
- [14 — First Deploy](15_first_deploy.md)
- [15 — Custom Domain & SSL](16_domain_ssl.md)
- [16 — Workload Identity Federation](17_wif.md)
- [17 — GitHub Actions CI/CD](18_github_actions.md)
- [18 — Quick Reference](19_quick_reference.md)