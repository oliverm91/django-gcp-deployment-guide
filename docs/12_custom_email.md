---
description: "Learn about custom email registration, costs involved, and how to set up email sending from Django before configuring human-facing inboxes."
image: assets/social-banner.png
---
# 12 — Bonus: Custom Email (@domain.cl)

← [Previous: 11 — Quick Reference](11_quick_reference.md)

Once you own your domain (e.g. `mycoolproject.cl`) from [Chapter 08](08_domain_ssl.md), you can create any email address under that name (e.g. `contact@mycoolproject.cl`). You don't "register" each individual address, but you do need to configure a service to manage them.

---

## 1. Core Concepts and Costs

### Do I have to pay for each address?
It depends on the usage:

- **For the Application (Automatic sending):** Generally **free** for low volumes (e.g., less than 300 emails/day with Brevo). You can invent any address like `notifications@your-domain.cl` at no extra cost.
- **For Humans (Inbox):** If you want to log into a Gmail-like interface to read and reply, it's generally **paid**. Google Workspace costs ~$6 USD per user per month.

### Configure DNS Records

Email identity is established entirely through your **DNS provider** (Cloudflare or GCP Cloud DNS). You must add these records so other servers know how to find you and trust your messages:

| Type | Name | Content / Value | Purpose |
|---|---|---|---|
| **MX** | `@` | `aspmx.l.google.com` (example) | Delivery: "Where do I send mail for this domain?" |
| **TXT** | `@` | `v=spf1 include:_spf.google.com ~all` | Authenticity: "Who is allowed to send mail for me?" |
| **TXT** | `google._domainkey` | `v=DKIM1; k=rsa; p=MIGfMA0GCS...` | Integrity: A digital signature per email. |
| **TXT** | `_dmarc` | `v=DMARC1; p=quarantine;` | Policy: "What to do if the others fail?" |

> 💡 **Note:** The values above are **examples**. The actual records (especially the long DKIM strings) will be provided to you by your chosen email provider (Brevo, Google Workspace, etc.) in the following sections.

---

## 2. Sending Email from the App (SMTP)

This is the priority for your Django app to be able to send registration confirmations or password recoveries. GCP explicitly blocks port 25, so you **must** use an external provider.

**Recommendation:** [Brevo](https://www.brevo.com/) (Free up to 300 emails/day).

### Steps:
1.  Create an account with the provider and add your domain.
2.  **SPF and DKIM Records (Critical):** The provider will give you text (TXT records) to paste into your DNS. These are your "digital signature" so Gmail doesn't send your mail to SPAM.
3.  **Configure Django:** Use SMTP credentials in your **Secret Manager** (Chapter 04) and connect them in `prod.py`.

---

## 3. Inboxes for Humans (Optional)

If you need to receive emails from customers and reply to them professionally, you need email hosting. The standard is **Google Workspace**.

### Configuration for Google Workspace:
1.  **Verification:** Google will ask for a TXT code in your DNS to prove you own the domain.
2.  **MX Records:** These records tell the internet: "if someone writes to this domain, deliver the message to Google's servers".

| Type | Host | Points to | Priority |
|---|---|---|---|
| MX | @ | `ASPMX.L.GOOGLE.COM` | 1 |
| MX | @ | `ALT1.ASPMX.L.GOOGLE.COM` | 5 |

### Free Alternative: Email Forwarding
If you use **Cloudflare**, you can use their **Email Forwarding** service for free:

1.  Enable "Email Routing" in the Cloudflare dashboard.
2.  Create a rule: `info@mycoolproject.cl` → `your-personal-gmail@gmail.com`.
3.  **Cost:** $0. You receive professional emails in your personal inbox. You cannot "reply as" the domain easily, but it's perfect for starting out.

---

## 4. Why is there no "Email" menu in GCP?
Google prefers you to use **Google Workspace** (which is a separate business product) or partners like SendGrid. In the GCP console, you **won't see** an option to create emails; everything is managed via DNS records and external SMTP credentials.

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
- 12 — Bonus: Custom Email (@domain.cl) (Current chapter)
- 13 — Bonus: Django Tasks (Overview)
  - [13.A — Cloud Tasks via HTTP](13_django_tasks_cloud_tasks.md)
  - [13.B — Embedded db_worker](13_django_tasks_embedded.md)
