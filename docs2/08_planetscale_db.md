---
description: "Create a PlanetScale database and use Terraform to configure a serverless VPC connection for secure Cloud Run access."
image: assets/social-banner.png
---

# 08 — PlanetScale Database

← [Previous: 07 — Artifact Registry](07_artifact_registry.md)

This chapter covers creating the PlanetScale database and using Terraform to configure a serverless VPC connection so Cloud Run can connect to PlanetScale securely.

---

## Create the PlanetScale database

### Via the web dashboard

1. Go to [app.planetscale.com](https://app.planetscale.com) and sign up
2. Click "New Database" → name it `mycoolproject`
3. Choose a region closest to your users (e.g., `us-east`)
4. Note the connection string — you'll need it in a moment

### Via the CLI

```bash
pscale auth login
pscale database create mycoolproject
pscale connection-string mycoolproject main --fetch
```

This gives you the connection string. Store it somewhere safe — you'll use it in the next section.

---

## Serverless VPC for PlanetScale

PlanetScale uses a serverless VPC connector to allow Cloud Run to connect without going over the public internet. We need to create this with Terraform.

### Create the Serverless VPC Access connector

Add to `infrastructure/main.tf`:

```hcl
# Serverless VPC Access connector (for PlanetScale connection)
resource "google_vpc_access_connector" "planetcale" {
  name          = "planetscale-connector"
  region        = var.region
  network       = "default"
  min_instances = 2
  max_instances = 10
  machine_type  = "e2-micro"

  # This allows Cloud Run to reach PlanetScale without going over public internet
  # PlanetScale provides an IP range for their serverless VPC
  reserved_ip_ranges = ["10.8.0.0/28"]
}

output "vpc_connector_name" {
  value = google_vpc_access_connector.planetcale.name
}
```

> **Note:** The `reserved_ip_ranges` should match your PlanetScale VPC configuration. If PlanetScale gives you a different IP range, use that instead. Check PlanetScale's documentation for the correct range.

Run `terraform apply` to create the connector.

---

## Create a Terraform resource for the connection (optional)

If PlanetScale provides a Terraform provider or you want to manage the connection string via Terraform, you can store it as a secret. But since PlanetScale manages the database, you create it via their dashboard and just store the connection string.

### Store connection string in Secret Manager

```hcl
# Secret for PlanetScale connection string
# Note: The actual value must be set outside of Terraform (use CLI or dashboard)
# This creates the secret structure that you'll populate
resource "google_secret_manager_secret" "database_url" {
  secret_id = "DATABASE_URL"

  replication {
    auto {}
  }
}

# Grant the service account access to read the secret
resource "google_secret_manager_secret_iam_member" "run_secret_accessor" {
  secret_id = google_secret_manager_secret.database_url.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member     = "serviceAccount:${google_service_account.run.email}"
}

output "database_url_secret_id" {
  value = google_secret_manager_secret.database_url.secret_id
}
```

---

## Update service account for VPC

The Cloud Run service needs the VPC connector to connect to PlanetScale. Add this to the service account creation later (chapter 11) or update your Cloud Run service:

```hcl
resource "google_cloud_run_service" "web" {
  # ... other config ...

  template {
    spec {
      # ... other spec ...

      # Use the VPC connector for outbound connections
      vpc_access {
        connector = google_vpc_access_connector.planetcale.name
        # Egress setting: route all traffic through VPC (for PlanetScale)
        egress = "ALL_traffic"
      }
    }
  }
}
```

---

## Alternative: Connect without VPC

If you don't want to use VPC (simpler but traffic goes over public internet), just use the connection string directly:

```bash
# Set the secret value directly
echo -n "postgres://user:password@aws.connect.psdb.cloud/mycoolproject?sslmode=require" \
  | gcloud secrets create DATABASE_URL --data-file=-
```

Cloud Run connects to PlanetScale over the public internet with SSL. This works fine for most use cases.

---

## Django DATABASE_URL

Django reads the database connection from `DATABASE_URL`. In `web/core/settings/prod.py`:

```python
import environ

env = environ.Env()

DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}
```

The `DATABASE_URL` environment variable is set from Secret Manager at container startup.

---

## PlanetScale with Django: caveats

1. **No foreign keys** — Use `on_delete=models.DO_NOTHING` or `db_constraint=False`
2. **No `SELECT FOR UPDATE`** — Use optimistic locking patterns
3. **Migrations** — Django migrations work fine, but use `--fake-initial` on first run if you have issues

Example Django model field:

```python
# Instead of:
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

# Use (for PlanetScale compatibility):
class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, db_constraint=False)
```

Most apps don't actually need enforced foreign keys — application-level referential integrity works fine.

---
## Managing branches via Terraform

You don't have to use Terraform for PlanetScale — branches and credentials can be created via the dashboard or CLI. You could just remember to create a branch when needed and delete it when done.

Using Terraform for branch management is helpful because:

- **Version control** — branch lifecycle is documented in code, not scattered across people's dashboards
- **Reviewability** — branch creation/deletion shows up in pull requests, so the team sees changes
- **Reproducibility** — if someone accidentally deletes a branch, you can recreate it from the Terraform file
- **Disaster recovery** — Terraform state shows exactly what branches existed, making recovery straightforward

Example Terraform configuration:

```hcl
provider "planetscale" {
  organization = "your-org"
}

resource "planetscale_postgres_branch" "development" {
  name       = "development"
  source_db  = "mycoolproject"
}
```

In this guide, branches and credentials are managed via Terraform to keep everything in version control.

---
## Summary: what we've created

- PlanetScale database (via their dashboard)
- Serverless VPC connector in GCP (via Terraform)
- Secret Manager secret for the connection string
- IAM binding for the service account to read the secret

---

## Navigation



- [01 — Introduction: What We're Building](01_introduction.md)
- [02 — Terraform Overview](02_terraform_overview.md)
- [03 — Cloud Services Explained](03_cloud_services.md)
- [04 — PlanetScale Database Explained](04_planetscale.md)
- [05 — Project Setup & Terraform State](05_project_setup.md)
- [06 — GCP Project & APIs](06_gcp_project.md)
- [07 — Artifact Registry](07_artifact_registry.md)
- 08 — PlanetScale Database (Current chapter)
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