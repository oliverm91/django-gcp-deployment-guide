# Review Notes — English Chapters (docs/*.md)

Generated: 2026-04-17. **Target: Django 6.0.** Focused on **bad practices, things that could be done better, and cost estimation accuracy**. Extra attention to `index.md` and `13_django_tasks.md`.

## Django 6.0 context (affects the review below)
- **`django.tasks` is in Django core** (merged from the reference `django-tasks` package in the 5.2/6.0 cycle per DEP-0014). This is the canonical background-task API going forward — see Chapter 13 notes.
- **Python**: Django 6.0 requires **Python 3.12+**. The guide's `python:3.12-slim` base image is the floor — consider `python:3.13-slim` for headroom.
- **PostgreSQL**: Django 6.0 requires **PostgreSQL 14+**. The guide's `POSTGRES_15` is fine.
- **`STORAGES` dict** (used in Chapter 05) has been the canonical form since 4.2; no changes needed.
- **`CSRF_TRUSTED_ORIGINS`** requirement (Chapter 08 note) continues to apply.
- Long-deprecated APIs removed in 6.0 (e.g. `default_app_config`, older `url()` alias paths) are not referenced anywhere in the guide — no action needed.

Legend:
- 🔴 **Critical** — factually wrong, broken command, or security issue
- 🟠 **Important** — bad practice or misleading
- 🟡 **Nice-to-have** — improvement opportunity
- 💰 **Cost** — estimation inaccuracy

---

## 🚨 Chapter 13 — `13_django_tasks.md` (major issues)

### 🔴 Identity crisis: "Django Tasks" vs `django-q2` — **must switch to Django 6.0's built-in `django.tasks`**
The chapter title says **Django Tasks**, but every code sample uses **`django-q2`** — a *different* library:
- `uv add django-q2`
- `from django_q import task`
- `Q_CLUSTER = {...}`
- `manage.py qcluster`
- Link points to `django-q2.readthedocs.io`

**Django 6.0 ships `django.tasks` in core** (per DEP-0014). Since this guide targets 6.0, the chapter should use the built-in API, not django-q2. Concretely:

```python
# settings/prod.py
INSTALLED_APPS += ["django.tasks"]

TASKS = {
    "default": {
        "BACKEND": "django.tasks.backends.database.DatabaseBackend",
    },
}
```

```python
# myapp/tasks.py
from django.tasks import task

@task()
def send_welcome_email(user_id): ...
```

```python
# calling site
from .tasks import send_welcome_email
send_welcome_email.enqueue(user.id)   # note: .enqueue(), not a bare call
```

Runner:
```bash
python manage.py db_worker      # built-in; replaces `qcluster`
```

Leaving the chapter on django-q2 while labelling it "Django Tasks" on a Django-6.0 guide is actively misleading.

---

### 🔴 Restructure the runner options: promote Cloud Tasks, drop the scheduled Cloud Run Job

The chapter's current two options don't fit a scale-to-zero Cloud Run design. Replace them with:

#### ✅ New **Option A (recommended): Cloud Tasks → HTTP endpoint on the Cloud Run web service**

- Producer (a Django view / service-layer call) enqueues a task by POSTing to a Cloud Tasks queue via `google-cloud-tasks`.
- Cloud Tasks delivers the task as an HTTP POST to a dedicated endpoint on the **same** Cloud Run service (e.g. `POST /internal/tasks/<task_name>/`). Cloud Run spins up on demand to serve it, then scales back to zero.
- Cloud Tasks handles retries with exponential backoff, per-queue concurrency caps, rate limits, and `scheduleTime` for delayed execution — all built in.
- Auth: Cloud Tasks attaches an **OIDC token** signed by a dedicated service account; the view verifies the token and rejects anything else.
- **Keeps `min-instances=0`** — aligns with the rest of the guide.
- **No DB polling** — nothing runs when no task is queued.
- **Cost** at low/medium volume: effectively free. Cloud Tasks gives **1 M operations/month free**, then $0.40 per million. A small app's task volume won't approach the free tier.

**Caveat — backend adapter:** `django.tasks` does not ship a first-party Cloud Tasks backend. Options:
- Use a third-party `django.tasks` Cloud Tasks backend if/when one is stable.
- Write a thin custom backend (~50 lines) that serializes the task call, enqueues via `google-cloud-tasks`, and wires an HTTP view to deserialize and invoke.
- Or bypass `django.tasks` for queueing and use Cloud Tasks directly for this subset of work.

**Other caveats to call out:**
- Task payload limit ≈ **100 KB** — pass IDs, fetch objects inside the handler.
- Handler must be **idempotent** — Cloud Tasks can deliver more than once.
- The HTTP view must complete within Cloud Run's **request timeout** (max 60 min on 2nd-gen, default 5 min). Jobs longer than that still belong in Cloud Run Jobs.
- Needs one more GCP API enabled (`cloudtasks.googleapis.com`) and one more IAM binding (`roles/cloudtasks.enqueuer` for the producer SA; the Cloud Tasks SA needs `roles/run.invoker` to call the handler).

#### ⚙️ New **Option B (fallback for long/batch work): embedded worker in the web service**

This is the **current Option A** demoted to Option B. Keep it in the chapter as an alternative for apps that:
- Don't want to write a backend adapter.
- Have tasks that exceed 100 KB payload, exceed the HTTP timeout, or need long-running streams.

When documenting it, add the two things the chapter currently misses:
- **`--no-cpu-throttling` is required** — without it the background worker is throttled to near-zero CPU between requests and will silently not run tasks.
- **Requires `--min-instances=1`** and **`--no-cpu-throttling`** — this roughly doubles the baseline web service cost (~$10–20/month), not "zero" as the current text claims.
- Use `exec` / `trap` in `start.sh` so SIGTERM reaches the worker on shutdown (otherwise tasks get killed on every deploy).

#### 🗑️ Delete the current **Option B (Cloud Run Job + Cloud Scheduler every minute)**

The chapter should **remove** this option entirely. Reasons:
- Cloud Tasks does the same job better: lower latency (seconds vs. up to 60 s), built-in backoff, no polling, cheaper at most volumes.
- A Cloud Scheduler cron that wakes up a worker every minute is the anti-pattern Cloud Tasks was designed to replace.
- Reduces the chapter's cognitive load — two clear options instead of three overlapping ones.

(If the user needs cron-style periodic work — nightly report, hourly cleanup — that's a separate concern and belongs in a short "scheduled tasks" sidebar that uses Cloud Scheduler → Cloud Run Job for genuinely periodic jobs, not as a polling mechanism for a task queue.)

---

### 🔴 Other commands in the current chapter that must be fixed regardless of option structure

- **Invalid command `gcloud run exec -it`** (Section 7): does not exist. There is no SSH-like exec on Cloud Run. Remove entirely.
- **Deprecated `gcr.io/...`** (Section 6): Container Registry has been shut down (2025). Use Artifact Registry path: `southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/...`.
- **Inconsistent region**: `--region us-central1` in §6/§7 vs. `southamerica-east1` everywhere else in the guide.
- **Invalid `gcloud builds submit --dockerfile` flag**: not a real flag. Use `cloudbuild.yaml` or rename the file. Also Cloud Build introduces a cost not mentioned elsewhere.
- **Dockerfile uses `pip install -r requirements.txt`** where the rest of the guide uses `uv` + `pyproject.toml` + `uv.lock`. Will not work with the project's structure.

### 🟠 Missing: DB-backend task queue load on Cloud SQL (if Option B is used)
`django.tasks` DatabaseBackend polls PostgreSQL continuously. On `db-f1-micro` (0.6 GB RAM):
- Keeps one DB connection busy 24/7.
- Generates constant logs.
- Can meaningfully reduce capacity for web requests.

This is another argument for Option A (Cloud Tasks): the DB sees zero load from idle task plumbing.

### 🟡 Graceful shutdown in the embedded runner (Option B)
If Option B is documented, the background `python manage.py db_worker &` is not forwarded SIGTERM on container shutdown — in-flight tasks are killed on every deploy. Use `trap` in `start.sh` to forward signals, or run the worker under a supervisor.

### 🟡 `gunicorn --threads 4` inconsistency
`start.sh` adds `--threads 4` but Chapter 06's Dockerfile doesn't. Unify the Gunicorn config or explain why threads are needed in the embedded-worker path.

---

## `index.md`

### 💰 Missing costs in the overview table
- **Egress bandwidth** — Cloud Storage serving public media files costs $0.08–$0.12/GB (can dominate cost if images are large and traffic grows). Not mentioned.
- **Cloud Run Jobs** — migrate job executions have a cost beyond the service itself (tiny but nonzero).
- **Cloud Tasks** (new for Ch 13 Option A) — 1 M operations/month free, then $0.40/M. Effectively free at this scale but worth listing.
- **Cloud Build** — if still referenced in Ch 13; has its own pricing ($0.003/build-min beyond free 120 min/day).
- **Cloud SQL storage + backups** — beyond the $7 compute, HDD storage ~$0.09/GB/month, backups ~$0.08/GB/month.

(Cloud Scheduler should drop out of the table once Ch 13's current Option B is removed.)

### 💰 Free-credits framing
*"New GCP accounts get $300 free credits — enough to run everything for months before paying anything."* — Correct but worth noting the credits **expire 90 days** after account creation, regardless of usage.

### 🟡 Chapter 13 in the index
The index lists *"13 — Bonus: Django Tasks — background job processing with Cloud Run Jobs"*. Two issues:
- "Django Tasks" is the right name **only if the chapter actually uses `django.tasks`** (Django 6.0 built-in). See §13 above — currently the code is django-q2.
- The one-liner description implies only Cloud Run Jobs, but the chapter's **recommended** approach is actually embedded. Align wording.

### 🟡 Navigation redundancy
The `index.md` lists chapters twice: once under "Setup order" (lines 44–56) with descriptions, and again under "📖 Chapters" (lines 110–122) without. One list is enough.

### 🟡 Inconsistent nav footers across chapters
Some chapters (02, 03, etc.) have a `← Previous` header link + a numbered nav list at the bottom. Index has no nav. Experience is uneven.

---

## `01_gcp_setup.md`

### 🔴 Broken multi-line bash commands
The service-account and IAM binding commands have **blank lines inside the backslash-continuation**:
```bash
gcloud iam service-accounts create mycoolproject-run-sa \

  --display-name="MyCoolProject Cloud Run SA"
```
A blank line terminates the line-continuation in bash — this command will fail. Same issue in all three `gcloud projects add-iam-policy-binding` blocks and in Chapter 07's `gcloud run services describe`. **Every reader copying these will hit errors.** Remove the blank lines.

### 🟠 Overly broad `roles/storage.objectAdmin`
`objectAdmin` grants delete rights on all buckets in the project. For a Django app, `roles/storage.objectUser` (newer, more granular) or the bucket-scoped equivalent is safer. Also, the binding is **project-wide**; scoping to just the two buckets is best practice.

### 🟡 Missing budget alert
A free-credit-aware reader should set a billing alert on day one. A one-liner `gcloud billing budgets create ...` or a note pointing to the Billing console would save a lot of pain.

### 🟡 No mention of `roles/run.admin` or Artifact Registry reader
The runtime SA doesn't need these, but a reader later wondering *"why did Cloud Run pull work without permissions?"* would benefit from a sentence: *"Cloud Run's own service agent handles image pulls automatically — your runtime SA only needs the runtime roles listed here."*

---

## `02_artifact_registry.md`

### 🟠 No image retention / cleanup policy
Every push adds a new layer set. Over months, the registry grows past the 0.5 GB free tier. Should add:
```bash
gcloud artifacts repositories set-cleanup-policies mycoolproject-repo \
  --location=southamerica-east1 \
  --policy=cleanup-policy.json
```
Or at least mention that old tags should be deleted periodically.

### 🟡 No vulnerability scanning mention
`containerscanning.googleapis.com` can auto-scan pushed images for CVEs. Worth a one-liner.

---

## `03_cloud_sql.md`

### 🔴 `db-f1-micro` is legacy / being phased out
Google is migrating Cloud SQL to **Enterprise** / **Enterprise Plus** editions with new machine types (shared-core is deprecated on Enterprise Plus, still available on Enterprise). The guide should either:
- Explicitly use Enterprise edition: `--edition=ENTERPRISE --tier=db-f1-micro`.
- Or move to the smallest Enterprise custom tier: `--tier=db-custom-1-3840` (~$25/month) and adjust the cost table.

### 🔴 Wrong claim about pausing
> *"Pausing the instance stops compute billing but still charges for storage."*

Cloud SQL does not have a "pause" feature. You can **stop** an instance with `--activation-policy=NEVER`, but storage is still billed. Either rephrase or explain how to actually stop-and-restart.

### 🟠 Missing deletion protection
Production databases should be created with `--deletion-protection`. Without it, one `gcloud sql instances delete` wipes the DB.

### 🟠 No PITR or backup retention trade-off
`--retained-backups-count=7` is mentioned, but point-in-time recovery (`--enable-point-in-time-recovery`) isn't. PITR gives second-level recovery at a small storage cost. At least mention it exists.

### 🟠 `DATABASE_URL` couples user+password+host
Storing the full URL in Secret Manager means you must rewrite the entire secret to rotate any one piece. Alternative: store password alone and build the URL in `settings.py`. More flexible, though more verbose.

### 🟡 No connection pooling mention
Django opens a fresh connection per request by default. On `db-f1-micro` (25 max connections), a couple of busy Cloud Run instances can starve the DB. Suggest `CONN_MAX_AGE` or PgBouncer.

---

## `04_secret_manager.md`

### 💰 Cost arithmetic is off
The chapter states: *"11 secrets... roughly $0.30/month total"*. Pricing is $0.06 per active secret version per month:
- 11 secrets × 1 version each × $0.06 = **$0.66/month**, not $0.30.
- Plus $0.03 per 10,000 access ops (usually free for this use).

### 🟠 Project-specific secrets baked into the universal guide
`DIDIT_API_KEY`, `DIDIT_WORKFLOW_ID`, `DIDIT_WEBHOOK_SECRET` are only relevant if the reader uses Didit KYC. Present as "example — adjust to your app's secrets".

### 🟡 No rotation guidance
Secret Manager supports rotation schedules. One paragraph would round out the chapter.

---

## `05_cloud_storage.md`

### 🔴 **Major privacy/security issue: public media bucket**
```bash
gsutil iam ch allUsers:objectViewer gs://mycoolproject-media
```
This makes **every user-uploaded file publicly readable by anyone with the URL**. Concerns:
- Combined with **Didit KYC secrets** elsewhere in the guide, a reader building a KYC flow would upload ID documents into this bucket. Those would be world-readable. Catastrophic privacy breach.
- Avatars and listing images *may* be fine public, but mixing them with sensitive uploads in one public bucket is dangerous.

Recommendation:
- Keep `mycoolproject-static` public (CSS/JS are fine).
- Make `mycoolproject-media` **private**. Serve via signed URLs (`blob.generate_signed_url(...)`) or proxy through Django.
- Add a third bucket or a prefix-based IAM policy for truly public media (avatars) vs private (KYC).

### 🟠 Uniform bucket-level access not set
Without `--uniform-bucket-level-access`, legacy ACLs are mixed with IAM, which is a known source of accidental public exposure. Always set it.

### 🟠 No CORS configuration
If the Django app ever posts FormData/fetch uploads to a presigned URL, CORS must be configured on the bucket. Not mentioned.

### 🟡 No CDN
Serving static directly from `storage.googleapis.com/<bucket>/` is fine but costs egress. A Load Balancer + Cloud CDN in front dramatically reduces egress cost and improves latency.

---

## `06_dockerfile.md`

### 🟠 Python base image minimum version
Django 6.0 requires Python 3.12+. `python:3.12-slim` is literally the floor — any future 6.x patch that drops 3.12 breaks the image. Prefer `python:3.13-slim` (or pin explicitly to the minor version you've tested). Also call out in the chapter *why* 3.12 is the floor, so readers don't downgrade.

### 🟠 Container runs as root
No `USER` directive. Best practice: create a non-root user and `USER app`. Reduces damage if the container is compromised.

### 🟠 Gunicorn started via `uv run` (not PID 1)
```dockerfile
CMD ["uv", "run", "gunicorn", ...]
```
`uv run` spawns a child process — `gunicorn` is not PID 1, so SIGTERM from Cloud Run may not reach it cleanly → ungraceful shutdowns and dropped requests during deploys. Use `exec` via a shell, or install into a venv and call the binary directly (`/app/.venv/bin/gunicorn ...`).

### 🟡 No multi-stage build
A multi-stage build (builder + distroless runtime) can cut the image further and reduce attack surface.

### 🟡 No HEALTHCHECK
Not required by Cloud Run, but useful for local `docker run` testing.

### 🟡 `.dockerignore` incomplete
Missing: `.github/`, `docs/`, `site/` (mkdocs build output). Including these bloats the build context.

### 🟡 Workers sizing
`--workers 2 --timeout 60` on 1 vCPU / 512 Mi is fine but not explained. Could mention threads or the `gthread` worker class for I/O-bound workloads.

---

## `07_first_deploy.md`

### 🔴 Superuser password passed as plain env var
```bash
--set-env-vars=DJANGO_SUPERUSER_EMAIL=admin@mycoolproject.cl,DJANGO_SUPERUSER_PASSWORD=<temp-password>
```
Env vars on Cloud Run Jobs are **visible in the console and logs**. The password persists on the Job definition. Should:
- Put `DJANGO_SUPERUSER_PASSWORD` in Secret Manager (temporarily) and use `--set-secrets`.
- Explicitly instruct to delete the Job right after: `gcloud run jobs delete createsuperuser --region=... --quiet`.

### 🟠 `--memory=512Mi` is tight
Django + Cloud SQL Auth Proxy sidecar + gunicorn workers = can easily exceed 512 MiB under load, triggering OOM kills. `1 Gi` is a safer default.

### 🟠 First-deploy command reuses `$IMAGE` without re-defining it in each section
Readers copying individual snippets will hit an empty variable. Repeat the `IMAGE=...` line in each block.

### 🟠 Same backslash-empty-line bug (see Chapter 01)
`gcloud run services describe` block has a blank line after `\`. Same fix.

### 🟡 No cold-start / CPU boost note
With `min-instances=0` and Cloud SQL proxy, cold starts can be **3–8 seconds**, not "1–2 s" as stated. `--cpu-boost` helps.

### 🟡 No cleanup step for the `createsuperuser` job
After use, the Job sits there with the password still embedded in its env vars.

---

## `08_domain_ssl.md`

### 🔴 Missing Django CSRF / proxy settings for the custom domain
Django 6.0 still requires `CSRF_TRUSTED_ORIGINS` to include `https://mycoolproject.cl` (the requirement was introduced in 4.0 and hasn't relaxed). Without it, every POST from the production site returns **403 CSRF verification failed**. Also needed:
```python
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```
None of this is mentioned. Readers will deploy, try to log in, and see CSRF errors they can't explain.

### 🟠 `gcloud run domain-mappings` caveats
- This API is **not available in all regions** (including, at times, `southamerica-east1`). Warn readers to check availability or fall back to a Global Load Balancer.
- The Global LB approach is more robust (multi-region, CDN-integrated) but costs ~$18/month for the forwarding rule — a cost the guide currently ignores.

### 🟡 `ghs.googlehosted.com` is the legacy target
Modern Cloud Run domain mappings often issue A/AAAA records. Text should say "copy the record gcloud shows you" rather than implying it's always that CNAME.

---

## `09_workload_identity.md`

### 🔴 **Missing `--attribute-condition` — severe security risk**
The provider is created with:
```bash
--attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository"
```
But **no `--attribute-condition`**. Google now requires an attribute condition on new providers (introduced 2024 in response to supply-chain incidents) — the setup shown here will actually **fail on new projects**.

Must add:
```bash
--attribute-condition="assertion.repository == 'YOUR_ORG/YOUR_REPO'"
```
And ideally also map `attribute.repository_owner=assertion.repository_owner`.

This is the single most important fix in the whole guide.

### 🟡 No mention of branch restriction
Binding by repo allows any branch in that repo to deploy. Better: `attribute.ref=assertion.ref` + condition `== 'refs/heads/main'`.

---

## `10_github_actions.md`

### 🔴 `astral-sh/setup-uv@v4` has no `working-directory` input
```yaml
- uses: astral-sh/setup-uv@v4
  with:
    working-directory: web
```
The action installs uv system-wide; there is no `working-directory` input. This step will fail at runtime. Remove `with:` and use `cd web` in the run steps.

### 🔴 Likely wrong test path
```yaml
run: cd web && uv run manage.py test web/tests --settings=core.settings.test
```
After `cd web`, `web/tests` resolves to `web/web/tests`. Probably meant `uv run manage.py test tests` or just `uv run manage.py test`.

### 🟠 No Docker layer cache on the runner
Every build rebuilds `uv sync` from scratch. Switch to `docker/build-push-action@v5` with `cache-from: type=registry,ref=...:cache` and `cache-to: type=registry,ref=...:cache,mode=max`.

### 🟠 No `concurrency:` block
Two quick pushes to `main` run two parallel deploy jobs. With migrations involved, this is dangerous. Add:
```yaml
concurrency:
  group: deploy-main
  cancel-in-progress: false
```

### 🟠 No uv cache
`uv sync --frozen` re-downloads wheels every run. `actions/cache` or `setup-uv`'s built-in cache option saves 30–60 s per test run.

### 🟡 No failure notification
A silently failing production deploy is the worst-case outcome. Add an `if: failure()` Slack/email step.

### 🟡 Static files collection is not automated
Chapter 05 mentions *"the GitHub Actions pipeline can run this automatically"* but the workflow here does **not** run `collectstatic`. If CSS/JS changes aren't synced to GCS on deploy, the site will 404 them. Either run collectstatic in CI or bake it into the Docker image build.

---

## `11_quick_reference.md`

### 🟡 Mostly fine, but
- `gcloud sql connect` requires the `gcloud` beta component on some platforms and authorized networks / a public IP on the instance. With the guide's Unix-socket-only setup this may not even work. Worth a caveat.
- The manual-deploy snippet re-runs migrate every time — fine, but consider noting that skipping migrate is safe if no migration files changed.

---

## `12_custom_email.md`

### 🟠 Google Workspace pricing out of date
Business Starter is **$7/user/month** in most regions (raised from $6 in 2023). Update the number.

### 🟠 DMARC recommendation too aggressive
`v=DMARC1; p=quarantine;` without first monitoring will cause legitimate mail to disappear. Best practice: start with `p=none` (monitor via `rua=mailto:...`), then `quarantine`, then `reject`.

### 🟡 Missing: Cloud Run port 25 block
Deserves its own note: GCP blocks outbound SMTP on port 25 always. Use 587 (STARTTLS) or 465 (SMTPS).

### 🟡 Missing: DMARC reporting addresses
`rua=` (aggregate reports) and `ruf=` (forensic) aren't mentioned. Without them, you never see deliverability results.

---

## Cross-cutting issues

### 🔴 Broken multi-line continuations
The pattern `\ <blank line> --flag=...` appears in at least 01 and 07. Every instance is a broken command for copy-paste. Do a grep sweep across all chapters.

### 🟠 Inconsistent region
Guide uses `southamerica-east1` everywhere **except** Chapter 13 which switches to `us-central1`. Pick one.

### 🟠 Inconsistent package manager
Guide uses `uv` everywhere **except** Chapter 13 Dockerfile snippets which use `pip`. Pick one.

### 🟠 No budget alert anywhere in the guide
For a guide aimed at new GCP users with $300 credits, a **single `gcloud billing budgets create`** snippet would prevent horror stories. Add to Chapter 01.

### 🟡 Architecture diagram referenced but not described
`index.md` shows `architecture.svg`; a one-paragraph textual description helps readers with screen readers or mobile renders.

---

## Priority ranking for fixes (highest-impact first)

1. 🔴 Chapter 09 — add `--attribute-condition` to WIF provider *(security)*.
2. 🔴 Chapter 05 — do not make the media bucket public; use signed URLs *(privacy/security)*.
3. 🔴 Chapter 13 — **swap django-q2 for Django 6.0's built-in `django.tasks`**, **restructure runner options**: promote **Cloud Tasks** to Option A (recommended, scale-to-zero friendly), demote current embedded runner to Option B, **delete** the Cloud Run Job + Cloud Scheduler option. Also fix broken commands (`gcr.io`, `gcloud run exec`, `--dockerfile`, Dockerfile `pip` vs `uv`).
4. 🔴 Chapter 01/07 — fix broken `\` + blank-line continuations.
5. 🔴 Chapter 08 — add `CSRF_TRUSTED_ORIGINS` and proxy SSL headers.
6. 🔴 Chapter 10 — fix invalid `setup-uv` input and wrong test path.
7. 🔴 Chapter 07 — move superuser password to Secret Manager, delete the job after.
8. 🟠 Chapter 03 — address `db-f1-micro` / Enterprise edition changes, add deletion protection.
9. 🟠 Chapter 06 — non-root user + `exec` PID-1 fix.
10. 💰 Index + Chapter 04 — fix secret-manager arithmetic, add egress/Cloud-Scheduler/Cloud-Build costs and 90-day credit expiry caveat.
