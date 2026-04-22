---
description: "Configure Workload Identity Federation so GitHub Actions can securely authenticate to GCP without storing JSON keys."
image: assets/social-banner.png
---

# 17 — Workload Identity Federation

← [Previous: 16 — Custom Domain & SSL](16_domain_ssl.md)

Workload Identity Federation lets GitHub Actions authenticate to GCP using short-lived tokens instead of long-lived JSON keys. This is more secure and requires no manual credential management.

---

## Why this matters

Without Workload Identity, GitHub Actions would need a JSON key file stored as a GitHub secret. This key:
- Never expires
- Can be leaked if the repo is compromised
- Requires manual rotation

With Workload Identity, GitHub Actions gets a short-lived token (valid ~1 hour) that it exchanges for GCP access. No permanent credentials stored anywhere.

---

## How it works

```
GitHub Actions workflow
    │
    ├── Requests OIDC token from GitHub's OIDC provider
    │     (proves: "I am workflow in YOUR_ORG/YOUR_REPO on branch main")
    │
    ├── Exchanges token with GCP for short-lived GCP access token
    │
    └── Uses GCP token to push images and deploy
```

The key security boundary: only your specific GitHub repo can impersonate your GCP service account.

---

## Setup (run in local terminal)

### Step 1: Create the Workload Identity Pool

```bash
PROJECT_NUMBER=$(gcloud projects describe mycoolproject-prod --format='value(projectNumber)')

gcloud iam workload-identity-pools create github-pool \
  --location=global \
  --display-name="GitHub Actions Pool"
```

### Step 2: Create the OIDC Provider

```bash
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --display-name="GitHub provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

### Step 3: Grant the service account permission

```bash
gcloud iam service-accounts add-iam-policy-binding \
  mycoolproject-run@mycoolproject-prod.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/YOUR_ORG/YOUR_REPO"
```

Replace `YOUR_ORG/YOUR_REPO` with your GitHub org and repo name (e.g., `octocat/mycoolproject`).

### Step 4: Get the provider resource name

```bash
gcloud iam workload-identity-pools providers describe github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --format="value(name)"
```

Output looks like:
```
projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider
```

**Copy this entire string** — you need it for GitHub secrets.

---

## Add GitHub Secrets

In your GitHub repo: **Settings → Secrets and variables → Actions → New repository secret**

| Secret name | Value |
|---|---|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider` |
| `GCP_SERVICE_ACCOUNT` | `mycoolproject-run@mycoolproject-prod.iam.gserviceaccount.com` |

---

## Terraform: Create the Workload Identity pool (optional)

Terraform can create the pool and provider:

```hcl
# Workload Identity Pool
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-pool"
}

# OIDC Provider
resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_location = "global"

  display_name = "GitHub provider"
  description  = "GitHub Actions OIDC provider"

  attribute_mapping = {
    "google.subject"         = "assertion.sub"
    "attribute.repository"   = "assertion.repository"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Grant the service account permission to impersonate
resource "google_service_account_iam_member" "run_workload_identity" {
  service_account_id = google_service_account.run.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${data.google_project.project.number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github.workload_identity_pool_id}/attribute.repository/${var.github_repo}"
}
```

---

## How GitHub Actions uses it

In the GitHub Actions workflow:

```yaml
- name: Authenticate to GCP
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
    service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}

- name: Set up gcloud
  uses: google-github-actions/setup-gcloud@v2

# Now gcloud and docker commands work
- docker build ...
- docker push ...
- gcloud run deploy ...
```

After this step, all `gcloud` and `docker push` commands in the workflow use the authenticated GCP credentials.

---

## Verify it works

Push a commit to main and watch the GitHub Actions workflow. If authentication works, you should see:

```
Authenticating to GCP with Workload Identity
gcloud credentials: OK
```

If it fails, double-check the `GCP_WORKLOAD_IDENTITY_PROVIDER` and `GCP_SERVICE_ACCOUNT` secrets are correct.

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
- 17 — Workload Identity Federation (Current chapter)
- [18 — GitHub Actions CI/CD](18_github_actions.md)
- [19 — Quick Reference](19_quick_reference.md)