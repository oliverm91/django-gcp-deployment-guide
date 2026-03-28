---
description: "Step 8: Map your custom domain name and automatically provision a managed SSL certificate for your Cloud Run service."
image: assets/social-banner.png
---
# 08 — Custom Domain & SSL

← [Previous: 07 — First Deploy](07_first_deploy.md)

> 💰 **Domain registration costs money — paid to your registrar, not GCP.**
> A `.cl` domain costs approximately $10–20/year depending on the registrar (NIC.cl charges ~$12/year). The domain is yours regardless of which hosting you use.
>
> ✅ **Everything else in this chapter is free.** GCP domain mapping, SSL certificate provisioning, and auto-renewal are all free. Cloudflare's DNS and DDoS protection are free on the free plan.

## What Cloud Run provides by default

After deploying, Cloud Run gives you a URL like:
```
https://mycoolproject-abc123-uc.a.run.app
```

This URL already has HTTPS with a Google-managed SSL certificate. For production you want to use your own domain (`mycoolproject.cl`) instead.

## How SSL works here

Cloud Run handles SSL termination — it presents your domain's certificate to browsers, decrypts incoming HTTPS traffic, and forwards plain HTTP to your container internally. You don't need Certbot, nginx, or any certificate management. Google provisions and auto-renews the certificate for free.

---

## Map your domain to Cloud Run

```bash
# Maps your custom domain to the Cloud Run service and begins SSL certificate provisioning.
# After running this, GCP will tell you which DNS record to add at your registrar.
# Result: GCP prints the required CNAME or A record — add it to your DNS provider.
gcloud run domain-mappings create \
  --service=mycoolproject \
  --domain=mycoolproject.cl \
  --region=southamerica-east1
```

This returns a DNS record to add — something like:

```
Add a CNAME record:
  mycoolproject.cl → ghs.googlehosted.com
```

Or an A record pointing to Google's IP. The exact record depends on whether it's a root domain or subdomain.

Check status (SSL provisioning takes a few minutes to up to an hour):

```bash
# Checks the status of the domain mapping and SSL certificate provisioning.
# Wait until certificateMode shows AUTOMATIC and mappingStatus shows ACTIVE.
# SSL provisioning takes a few minutes to up to an hour after DNS propagates.
gcloud run domain-mappings describe \
  --domain=mycoolproject.cl \
  --region=southamerica-east1
```

Wait until `certificateMode` shows `AUTOMATIC` and `mappingStatus` shows `ACTIVE`.

---

## DNS setup (at your registrar or Cloudflare)

If using **Cloudflare** (recommended — free DDoS protection, bot filtering):

1. Add your domain to Cloudflare (free plan)
2. Point your registrar's nameservers to Cloudflare's
3. In Cloudflare DNS, add the record GCP gave you
4. Set proxy to **DNS only (grey cloud)** — Cloud Run manages SSL itself; Cloudflare proxying would interfere with certificate provisioning

If using your registrar directly (NIC.cl, Namecheap, etc.):

1. Log in to your registrar's DNS management panel
2. Add the CNAME or A record GCP provided

---

## www redirect

To also handle `www.mycoolproject.cl`:

```bash
# Maps the www subdomain to the same service, so www.mycoolproject.cl also works.
gcloud run domain-mappings create \
  --service=mycoolproject \
  --domain=www.mycoolproject.cl \
  --region=southamerica-east1
```

Or add a `CNAME www → mycoolproject.cl` in your DNS and let Cloudflare/registrar handle the redirect.

---

## Update ALLOWED_HOSTS

Once the domain is live, update the Cloud Run service to include both the custom domain and the original `.run.app` URL:

```bash
# Updates the ALLOWED_HOSTS env var on the running service without a full redeploy.
# Django rejects requests with an unrecognised Host header — this prevents that 400 error.
# Cloud Run creates a new revision automatically when env vars change.
gcloud run services update mycoolproject \
  --region=southamerica-east1 \
  --update-env-vars=ALLOWED_HOSTS="mycoolproject.cl,www.mycoolproject.cl"
```

`ALLOWED_HOSTS` is Django's security setting that rejects requests with an unrecognised `Host` header — prevents HTTP Host header attacks.

---

## 📖 Navigation

- [01 — GCP Project Setup](01_gcp_setup.md)
- [02 — Artifact Registry](02_artifact_registry.md)
- [03 — Cloud SQL (PostgreSQL Database)](03_cloud_sql.md)
- [04 — Secret Manager](04_secret_manager.md)
- [05 — Cloud Storage (Media & Static Files)](05_cloud_storage.md)
- [06 — Dockerfile](06_dockerfile.md)
- [07 — First Deploy](07_first_deploy.md)
- **08 — Custom Domain & SSL** (current chapter)
- [09 — Workload Identity Federation (Keyless GitHub Actions Auth)](09_workload_identity.md)
- [10 — GitHub Actions CI/CD Pipeline](10_github_actions.md)
- [11 — Quick Reference](11_quick_reference.md)
