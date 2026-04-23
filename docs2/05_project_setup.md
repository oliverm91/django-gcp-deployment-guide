---
description: "Set up your local environment for Terraform, initialize your project, and configure remote state storage in GCP."
image: assets/social-banner.png
---

# 05 — Project Setup & Terraform State

← [Previous: 04 — PlanetScale Database Explained](04_planetscale.md)

Before we write any Terraform configuration, we need to set up the project structure and understand where Terraform stores its state.

---

## The project directory

We need a directory for Terraform files. Inside your Django project, create an `infrastructure/` directory:

```bash
cd mycoolproject
mkdir -p infrastructure
cd infrastructure
```

This is where all Terraform files will live. The structure:

```
mycoolproject/
├── web/                    # Django app
│   ├── core/
│   ├── accounts/
│   └── ...
├── infrastructure/         # Terraform files (this guide's focus)
│   ├── main.tf
│   ├── variables.tf
│   ├── terraform.tfvars    # NOT committed to git
│   ├── .terraform/
│   └── terraform.tfstate   # Local for now (remote later)
└── .github/
    └── workflows/
```

---

## The state file problem

Terraform needs to remember what it created. It does this in a **state file** (`terraform.tfstate`).

If you work alone, you can store it locally. But if you work with a team or want to destroy and recreate infrastructure reliably, the state needs to be stored remotely — in GCP Cloud Storage.

### Why remote state?

- **Team collaboration** — everyone reads the same state
- **Locking** — prevents concurrent applies from breaking things
- **Durability** — survives your laptop being lost or reformatted

### Create a GCS bucket for Terraform state

We'll create this bucket manually (it's the chicken-and-egg problem: Terraform needs state, but we need Terraform to create infrastructure to store state). So we create the bucket with `gcloud`, then configure Terraform to use it.

Run this **once** from your local terminal:

```bash
# Create a GCS bucket to store Terraform state
# State must live in a unique bucket — use your project name and a suffix
gsutil mb -l southamerica-east1 gs://mycoolproject-terraform-state

# Enable versioning so we can recover previous state if needed
gsutil versioning set on gs://mycoolproject-terraform-state

# Check it exists
gsutil ls
```

Now we have somewhere to store state. But we need Terraform itself to create the rest of the infrastructure — so we initialize Terraform first with local state, then migrate to remote state.

---

## Create the Terraform configuration files

Create `infrastructure/variables.tf`:

```hcl
variable "project_id" {
  type        = string
  description = "The GCP project ID"
}

variable "region" {
  type        = string
  description = "GCP region for all resources"
  default     = "southamerica-east1"
}

variable "project_number" {
  type        = string
  description = "The GCP project number"
}
```

Create `infrastructure/terraform.tfvars` (example — replace with your values):

```hcl
project_id    = "mycoolproject-prod"
region        = "southamerica-east1"
```

Create `infrastructure/main.tf`:

```hcl
terraform {
  required_version = ">= 1.5.0"

  # Local state for now — we'll switch to remote after first apply
  # Uncomment the backend block later to use GCS
  # backend "gcs" {
  #   bucket = "mycoolproject-terraform-state"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
```

---

## Initialize Terraform

```bash
cd infrastructure
terraform init

# You should see:
# - Initializing provider plugins...
# - Terraform has been successfully initialized!
```

This downloads the GCP provider plugin and sets up the working directory.

---

## Plan and apply

### Get your project number

Terraform needs the project number (different from project ID). Get it:

```bash
gcloud projects describe mycoolproject-prod --format='value(projectNumber)'
```

Use this value in your `terraform.tfvars`:

```hcl
project_id      = "mycoolproject-prod"
region          = "southamerica-east1"
project_number  = "123456789012"  # Replace with your actual number
```

### Run terraform plan

```bash
terraform plan
```

This shows what Terraform will create. Since we only have the provider and no resources yet, it will say "No changes."

### Store state in GCS (after confirming it works)

Once you have resources, migrate to remote state:

```hcl
# Uncomment the backend block in main.tf
terraform {
  backend "gcs" {
    bucket = "mycoolproject-terraform-state"
    prefix = "terraform/state"
  }
}
```

Then migrate:

```bash
terraform init -migrate-state
```

---

## Directory structure for the rest of this guide

In the following chapters, we'll add resources to `main.tf` incrementally. For now, start with this structure:

```
infrastructure/
├── main.tf           # Empty (provider + backend)
├── variables.tf      # Variable declarations
├── terraform.tfvars  # Actual values (not in git)
└── .terraform/       # Provider plugins (auto-generated)
```

---

## Important: terraform.tfvars

The `terraform.tfvars` file contains actual values — project ID, region, and eventually secrets. **Never commit this file to git.** Add it to `.gitignore`:

```bash
echo "infrastructure/terraform.tfvars" >> .gitignore
```

The variable declarations go in `variables.tf` (which IS committed). The actual values go in `terraform.tfvars` (which is NOT committed).

---

## Navigation



- [01 — Introduction: What We're Building](01_introduction.md)
- [02 — Terraform Overview](02_terraform_overview.md)
- [03 — Cloud Services Explained](03_cloud_services.md)
- [04 — PlanetScale Database Explained](04_planetscale.md)
- 05 — Project Setup & Terraform State (Current chapter)
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
- [19 — Quick Reference](19_quick_reference.md)