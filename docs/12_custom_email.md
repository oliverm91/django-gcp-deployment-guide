---
description: "Learn how to set up professional @domain.cl email addresses and configure transactional email for your Django app using DNS records across GCP and external providers."
image: assets/social-banner.png
---
# 12 — Bonus: Custom Email (@domain.cl)

← [Previous: 11 — Quick Reference](11_quick_reference.md)

Having a custom email like `info@mycoolproject.cl` is essential for credibility. There are two types of email setups you need:

1.  **Professional Email (Inbox):** For you to send/receive mail (like Gmail but for your domain).
2.  **Transactional Email (SMTP):** For the Django app to send automated emails (password resets, welcome notes).

## Why is there no "Email" menu in GCP?

One of the most common points of confusion: **GCP does not provide a native email hosting service** (like Amazon SES). Instead, Google offers **Google Workspace** (as a separate business service) or partners with 3rd party providers like **SendGrid/Brevo**.

### The Port 25 Trap
Google Cloud **blocks outgoing traffic on port 25** for all Cloud Run and Compute Engine resources to prevent spam.
- **You cannot** use port 25.
- **You MUST** use port **587** (TLS) or **465** (SSL) in your Django settings.
- There is no "Firewall rule" to unblock port 25 for standard accounts.

---

## 1. Professional Email (Inboxes for humans)

GCP doesn't host mailboxes. The industry standard is **Google Workspace**.

### Configuration
1.  Sign up at [workspace.google.com](https://workspace.google.com/).
2.  **Domain Verification:** Google will ask you to add a `TXT` record to your DNS (Chapter 08).
3.  **MX Records:** These tell the world where to deliver mail. You must add these records to your DNS provider (Cloudflare/NIC.cl).

| Type | Host | Points to | Priority |
|---|---|---|---|
| MX | @ | `ASPMX.L.GOOGLE.COM` | 1 |
| MX | @ | `ALT1.ASPMX.L.GOOGLE.COM` | 5 |

---

## 2. Transactional Email (App automated mail)

Google Cloud prevents sending mail directly from Cloud Run via port 25 for security. You **must** use a 3rd party SMTP provider.

**Recommendation:** [Brevo](https://www.brevo.com/) (formerly Sendinblue) has a generous free tier (300 emails/day).

### Setup steps:
1.  Create a Brevo account and verify your domain.
2.  **DKIM/SPF Records:** Brevo will give you `TXT` records. These are "signatures" that prove the email actually came from you, preventing it from going to SPAM.
3.  **SMTP Credentials:** Brevo will provide an SMTP Server, Port, User, and Password.

---

## 3. Update Django Secrets

Take the SMTP credentials from Brevo and add them to **Secret Manager** (Chapter 04):

```bash
# Update your secrets with Brevo credentials
echo -n "smtp-relay.brevo.com" | gcloud secrets versions add EMAIL_HOST --data-file=-
echo -n "587"                  | gcloud secrets versions add EMAIL_PORT --data-file=-
echo -n "your-brevo-user"      | gcloud secrets versions add EMAIL_HOST_USER --data-file=-
echo -n "your-brevo-password"  | gcloud secrets versions add EMAIL_HOST_PASSWORD --data-file=-
```

In your `web/core/settings/prod.py`, ensure these are wired:

```python
# web/core/settings/prod.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'MyCoolProject <info@mycoolproject.cl>'
```

---

## 4. Why SPF and DKIM matter
If you don't add these DNS records, Gmail and Outlook will likely block your emails:
- **SPF:** A "whitelist" of servers allowed to send mail for your domain.
- **DKIM:** A cryptographic signature for every email.
- **DMARC:** A policy telling others what to do if SPF/DKIM fails (usually "quarantine" or "reject").

---

## 📖 Navigation

- [01 — GCP Project Setup](01_gcp_setup.md)
- [02 — Artifact Registry](02_artifact_registry.md)
- [03 — Cloud SQL (PostgreSQL Database)](03_cloud_sql.md)
- [04 — Secret Manager](04_secret_manager.md)
- [05 — Cloud Storage (Media & Static Files)](05_cloud_storage.md)
- [06 — Dockerfile](06_dockerfile.md)
- [07 — First Deploy](07_first_deploy.md)
- [08 — Custom Domain & SSL](08_domain_ssl.md)
- [09 — Workload Identity Federation (Keyless GitHub Actions Auth)](09_workload_identity.md)
- [10 — GitHub Actions CI/CD Pipeline](10_github_actions.md)
- [11 — Quick Reference](11_quick_reference.md)
- [12 — Bonus: Custom Email (@domain.cl)](12_custom_email.md)
