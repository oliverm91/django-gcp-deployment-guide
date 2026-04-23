---
description: "Map your custom domain to Cloud Run and get a free managed SSL certificate."
image: assets/social-banner.png
---

# 16 — Custom Domain & SSL

← [Previous: 15 — First Deploy](15_first_deploy.md)

Cloud Run gives you a URL like `https://mycoolproject-abc123-uc.a.run.app` with HTTPS already enabled. This chapter shows how to use your own domain instead.

---

## How SSL works with Cloud Run

Cloud Run handles SSL automatically via Google-managed certificates. You just point your domain to Cloud Run and GCP provisions and renews the certificate for free.

Two options:

| Setup | Who manages SSL | Notes |
|---|---|---|
| Cloudflare DNS only (grey cloud) | GCP | Simple, free, certificate from Google |
| Cloudflare proxied (orange cloud) | Cloudflare | Adds WAF/DDoS protection, but more complex |

This guide uses DNS only (grey cloud) — simplest setup.

---

## Map domain to Cloud Run

```bash
# Map your domain to the Cloud Run service
gcloud run domain-mappings create \
  --service=mycoolproject \
  --domain=mycoolproject.com \
  --region=southamerica-east1
```

This outputs a DNS record to add. Something like:
```
CNAME: mycoolproject.com → ghs.googlehosted.com
```

---

## Add DNS record

Add the DNS record at your registrar or in Cloudflare.

### Cloudflare setup

1. Add your domain to Cloudflare (free plan)
2. Set nameservers at your registrar to Cloudflare's
3. Add the CNAME record Cloud Run gave you
4. Set proxy mode to **DNS only** (grey cloud) ☁️

> **Important:** Use grey cloud (DNS only), not orange (proxied). Orange cloud makes Cloudflare terminate SSL, which breaks GCP's certificate provisioning and causes errors.

### Direct registrar setup

Add the CNAME or A record that `gcloud run domain-mappings create` told you about.

---

## Wait for SSL certificate

SSL provisioning takes a few minutes to up to an hour after DNS propagates.

Check status:

```bash
gcloud run domain-mappings describe \
  --domain=mycoolproject.com \
  --region=southamerica-east1
```

Look for `certificateMode: AUTOMATIC` and `mappingStatus: ACTIVE`.

---

## Update ALLOWED_HOSTS

Once the domain is live, update Cloud Run to accept requests from it:

```bash
gcloud run services update mycoolproject \
  --region=southamerica-east1 \
  --update-env-vars=ALLOWED_HOSTS="mycoolproject.com,www.mycoolproject.com,mycoolproject-abc123-uc.a.run.app"
```

Django's `ALLOWED_HOSTS` rejects requests with unknown `Host` headers — this prevents HTTP Host header attacks.

---

## Add www subdomain

To also handle `www.mycoolproject.com`:

```bash
gcloud run domain-mappings create \
  --service=mycoolproject \
  --domain=www.mycoolproject.com \
  --region=southamerica-east1
```

Add another CNAME record: `www.mycoolproject.com → mycoolproject.com` (or the same `ghs.googlehosted.com` target).

---

## Terraform configuration for domain mapping

Unfortunately, domain mappings cannot be created with Terraform (GCP doesn't support it in the Google provider yet). Use the `gcloud` CLI or GCP Console for this step.

But you can add the DNS record via Terraform if you're using Cloudflare:

```hcl
# Cloudflare provider (separate from GCP)
provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

resource "cloudflare_record" "www" {
  zone_id = var.cloudflare_zone_id
  name    = "www"
  value   = "ghs.googlehosted.com"
  type    = "CNAME"
  proxied = false  # Grey cloud — DNS only
}
```

---

## Cost notes

| Item | Cost |
|---|---|
| Domain registration | ~$10–15/year (paid to registrar, not GCP) |
| SSL certificate | Free (managed by GCP) |
| Cloudflare DNS | Free (on free plan) |
| Cloudflare proxied | Free (but breaks GCP SSL — use grey cloud) |

---

## Verify the site works

```bash
curl https://mycoolproject.com/health/
```

Should return `{"status": "ok"}`.

---

## Navigation



- [01 — Introduction: What We're Building](01_introduction.md)
- [02 — Terraform Overview](02_terraform_overview.md)
- [03 — Cloud Services Explained](03_cloud_services.md)
- [04 — PlanetScale Database Explained](04_planetscale.md)
- [05 — Project Setup & Terraform State](05_project_setup.md)
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
- 16 — Custom Domain & SSL (Current chapter)
- [17 — Workload Identity Federation](17_wif.md)
- [18 — GitHub Actions CI/CD](18_github_actions.md)
- [19 — Quick Reference](19_quick_reference.md)