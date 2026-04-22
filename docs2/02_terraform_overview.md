---
description: "Understand what Terraform is, how it works, and the core concepts you need to use it effectively."
image: assets/social-banner.png
---

# 02 — Terraform Overview

← [Previous: 01 — Introduction: What We're Building](01_introduction.md)

If you've never used Terraform before, this chapter gives you everything you need to understand how it works before we start writing configuration files.

---

## What is Terraform?

Terraform is an **Infrastructure as Code (IaC)** tool made by HashiCorp. Instead of clicking around a web console or running CLI commands, you write configuration files that describe the infrastructure you want. Terraform then creates, updates, and destroys resources to match.

Think of it like a recipe: you describe the dish, Terraform does the cooking.

**Why not just use `gcloud` commands?**

- `gcloud` commands are imperative — "do this thing now"
- Terraform is declarative — "this is what I want the world to look like"

With imperative tools, you have to remember the steps and the order. With Terraform, you just describe the desired end state and it figures out how to get there.

---

## Core concepts

### Providers

A **provider** is a plugin that Terraform uses to interact with a specific service. For this guide we use:

- `google` — the GCP provider (creates GCP resources)
- `hashicorp/random` — generates random values (useful for unique names)
- `hashicorp/local` — works with local files
- `planetscale` — manages PlanetScale branches and credentials

Providers are defined at the top of your Terraform files. You'll see something like:

```hcl
provider "google" {
  project = "my-project"
  region  = "southamerica-east1"
}
```

This tells Terraform: "I'm working with GCP, project is `my-project`, default region is `southamerica-east1`."

### Why PlanetScale provider?

The PlanetScale provider is optional — you could create branches and credentials via the dashboard or CLI and manage them manually. If you do that, you just remember to create a branch when needed and delete it when done.

Using Terraform for branch management is helpful because:

- **Version control** — branch lifecycle is documented in code, not scattered across people's dashboards
- **Reviewability** — branch creation/deletion shows up in pull requests, so the team sees changes
- **Reproducibility** — if someone accidentally deletes a branch, you can recreate it from the Terraform file
- **Disaster recovery** — Terraform state shows exactly what branches existed, making recovery straightforward

In this guide: the initial database is created manually (via dashboard or CLI), but branches and credentials are managed via Terraform.

### Resources

A **resource** is a piece of infrastructure that Terraform manages. Examples: a Cloud Run service, a Storage bucket, a Secret Manager secret.

Resources look like this:

```hcl
resource "google_storage_bucket" "static" {
  name     = "my-project-static"
  location = "southamerica-east1"
}
```

This says: "Create a resource of type `google_storage_bucket` called `static`. Set its `name` to `my-project-static` and `location` to `southamerica-east1`."

The first part (`google_storage_bucket`) tells Terraform which provider to use. The second part (`static`) is just a name you use to reference this resource within your Terraform code.

### Variables

**Variables** let you parameterize your Terraform configuration. Instead of hardcoding values, you define them once and reuse them:

```hcl
variable "project_id" {
  type        = string
  description = "The GCP project ID"
}
```

Then you use `var.project_id` anywhere you need that value. This makes your Terraform files more flexible and reusable.

### Output values

**Outputs** print useful values after `terraform apply` completes. They're often used to display URLs or connection strings:

```hcl
output "bucket_url" {
  value = "https://storage.googleapis.com/${google_storage_bucket.static.name}"
}
```

---

## The workflow

### 1. Write configuration

Create `.tf` files that describe your infrastructure. Start with the provider and resources.

### 2. Initialize

```bash
terraform init
```

This downloads the provider plugins and sets up the working directory.

### 3. Plan

```bash
terraform plan
```

Terraform shows what it will create, update, or destroy — before making any actual changes. Review this output carefully.

### 4. Apply

```bash
terraform apply
```

Terraform creates or updates resources to match your configuration. Type `yes` when prompted.

### 5. Inspect state

```bash
terraform show          # See current state
terraform state list    # List all resources
```

---

## State

Terraform stores what it created in a **state file**. This is how it knows what's real versus what's in your configuration files.

### Local vs remote state

- **Local state** — stored on your laptop (risky for teams, lost if laptop dies)
- **Remote state** — stored in cloud storage (GCS bucket), shared across team

For this guide, we store state in a GCP Cloud Storage bucket so everyone on the team uses the same state.

### State file tips

- **Never edit state manually** — let Terraform manage it
- **Store state remotely** — especially when working with a team
- **State contains sensitive values** — it shows actual resource names, sometimes IDs

---

## Modules

**Modules** are reusable Terraform templates. Instead of copying the same resource definitions across projects, you package them as a module.

For this guide, we keep things simple and write Terraform directly in `main.tf`. As you grow, you might extract common patterns into modules.

---

## Installing Terraform

If you haven't installed Terraform yet:

```bash
# macOS (Homebrew)
brew install terraform

# Linux
curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list
apt update && apt install terraform

# Windows: download from terraform.io/downloads and add to PATH

# Verify
terraform --version
```

---

## Navigation



- [01 — Introduction: What We're Building](01_introduction.md)
- 02 — Terraform Overview (Current chapter)
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
- [17 — Workload Identity Federation](17_wif.md)
- [18 — GitHub Actions CI/CD](18_github_actions.md)
- [19 — Quick Reference](19_quick_reference.md)