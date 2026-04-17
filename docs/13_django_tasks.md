---
description: "Add background job processing to Django using Django Tasks — with two runner options: embedded or separate Cloud Run Job."
image: assets/social-banner.png
---
# 13 — Bonus: Django Tasks

← [Previous: 12 — Bonus: Custom Email](12_custom_email.md)

Most Django apps eventually need to run code **outside** the request-response cycle: sending emails, generating reports, processing images, cleaning up old data. These are background jobs.

---

## 1. Django Tasks

[Django Tasks](https://django-q2.readthedocs.io/) is a lightweight background task queue built on Django's own ORM. It's not as powerful as Celery, but it's **good enough for roughly 80% of apps** and requires far less infrastructure to run.

### Django Tasks vs. Celery

| Feature | Django Tasks | Celery |
|---|---|---|
| Setup complexity | Low (just another Django app) | High (needs Redis/RabbitMQ + workers) |
| Reliability | Good for low-to-medium volume | Production-grade, handles millions |
| Monitoring | Basic | Flower, detailed dashboards |
| Infrastructure cost | Low | High (needs a message broker + runner) |

**Use Django Tasks when:** you have simple jobs (send email, generate PDF, crawl a page), moderate traffic, and don't want to manage extra infrastructure.

**Use Celery when:** you have heavy workloads, complex chains/orchestration, or need guarantees that every job is processed even under extreme load.

For most Django side projects and even small startups, Django Tasks is the pragmatic choice.

---

## 2. Install and Configure

```bash
uv add django-q2
```

In your `settings/prod.py`:

```python
# Q_CLUSTER setup — this makes Django Tasks work
Q_CLUSTER = {
    "name": "mycoolproject",
    "workers": 4,
    "timeout": 60,
    "orm": "default",  # Uses Django ORM as the queue backend
}

# Optional: retry on failure
Q_CLUSTER["reconnect"] = 10  # seconds
```

That's it — Django Tasks stores tasks in your existing PostgreSQL database. No Redis needed.

---

## 3. Writing Tasks

Create a file like `mycoolproject/tasks.py`:

```python
from django_q import task

@task()
def send_welcome_email(user_id):
    from users.models import User
    from django.core.mail import send_mail

    user = User.objects.get(id=user_id)
    send_mail(
        subject="Welcome to MyCoolProject!",
        message=f"Hi {user.first_name}, welcome aboard!",
        from_email="noreply@mycoolproject.cl",
        recipient_list=[user.email],
    )
```

Call it from anywhere in your code:

```python
from .tasks import send_welcome_email

# Fire and forget — returns immediately, runs in background
send_welcome_email(user.id)
```

### Schedule recurring tasks

In `django_q.py` or `management/commands/`:

```python
from django_q import schedule

# Run every hour
schedule("mycoolproject.tasks.cleanup_old_sessions", schedule_type="H")

# Run every day at 3am
schedule("mycoolproject.tasks.generate_daily_report", schedule_type="D", time=3)
```

---

## 4. Runner Options

Django Tasks needs a **runner process** running to pick up and execute queued jobs. Without it, tasks pile up and never run. Here are two approaches:

### Option A: Embedded in Your Web Service (Recommended — Free)

Run qcluster as a background thread **inside your existing web service container**. Since your Cloud Run web service already runs with `min_instances=1` (always warm), the runner costs nothing extra.

| | |
|---|---|
| **Pros** | Zero additional cost. No extra infrastructure. Tasks process instantly. |
| **Cons** | Runner shares CPU/memory with web requests. Heavy task loads can affect response times. If web service restarts, qcluster restarts too. |

### Option B: Separate Cloud Run Job

Deploy qcluster as a **separate Cloud Run Job** triggered by Cloud Scheduler every minute.

| | |
|---|---|
| **Pros** | Isolated from web service — heavy tasks don't affect request latency. Web service can scale to zero independently. |
| **Cons** | Expensive at ~$20–30/month due to frequent cold starts (1440 triggers/day). Latency up to 60s before tasks execute. More infrastructure to manage. |

**Recommendation:** Start with Option A. Upgrade to Option B only if your task workload grows to the point where it interferes with web request performance.

---

## 5. Option A: Embedded Runner (Implementation)

Since your Cloud Run web service is always warm (`min_instances=1`), run qcluster in the same container as a background process.

### Modify your entrypoint

Create a custom start script that launches both gunicorn and qcluster:

```bash
#!/bin/bash
# start.sh — run both gunicorn (web) and qcluster (task runner) together

# Start qcluster in background
python manage.py qcluster &
QCLUSTER_PID=$!

# Start gunicorn (waits for it to exit)
exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:8080 \
    --workers 2 \
    --threads 4 \
    --timeout 60 \
    --log-file -
```

Make it executable:

```bash
chmod +x start.sh
```

### Update your Dockerfile

Update your `Dockerfile` to use the custom entrypoint:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Use custom start script instead of running gunicorn directly
CMD ["./start.sh"]
```

### Update Cloud Run configuration

Ensure your web service has `min-instances=1` so qcluster stays warm:

```bash
gcloud run services update mycoolproject \
    --region=southamerica-east1 \
    --min-instances=1
```

That's it. On every web service deployment, qcluster starts automatically alongside gunicorn and processes tasks as they arrive. No additional Cloud Run resources, no Cloud Scheduler, no extra cost.

---

## 6. Option B: Separate Cloud Run Job

If you need isolation (heavy task workloads) or want your web service to scale to zero independently, use a separate Cloud Run Job.

### Step 1: Create a separate service account

```bash
gcloud iam service-accounts create django-q-runner \
    --display-name="Django Q Runner"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:django-q-runner@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"
```

### Step 2: Build a job-ready Docker image

Create `Dockerfile.job`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "manage.py", "qcluster"]
```

Build and push:

```bash
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/mycoolproject-job:v1 \
    --dockerfile Dockerfile.job
```

### Step 3: Create the Cloud Run Job

```bash
gcloud run jobs create django-q-cluster \
    --image gcr.io/$PROJECT_ID/mycoolproject-job:v1 \
    --service-account django-q-runner@$PROJECT_ID.iam.gserviceaccount.com \
    --region us-central1 \
    --max-retries 2
```

### Step 4: Schedule the job every minute

Cloud Run Jobs don't have built-in cron — use Cloud Scheduler:

```bash
gcloud scheduler jobs create http django-q-trigger \
    --schedule="* * * * *" \
    --uri=https://run.googleapis.com/v2/projects/$PROJECT_ID/locations/us-central1/jobs/django-q-cluster/run \
    --http-method POST \
    --oauth-service-account-email django-q-runner@$PROJECT_ID.iam.gserviceaccount.com
```

> 💡 **Why every minute?** Django Tasks stores scheduled tasks with a `next_run_time`. The runner only processes tasks that are due. Running every minute is cheap and responsive enough for most apps.

**Cost warning:** This triggers ~43,200/month, costing ~$20–30/month. Consider Option A instead.

---

## 7. Running Tasks Immediately (On-Demand)

### Option A (embedded runner)

Tasks execute immediately when enqueued — no extra step needed:

```python
send_welcome_email(user.id)  # executes within seconds
```

To force an immediate execution of scheduled tasks:

```bash
# Executes inside the running container (no new deployment needed)
gcloud run exec -it mycoolproject --region=southamerica-east1 -- python manage.py qcluster
```

### Option B (Cloud Run Job)

Trigger the job manually:

```bash
gcloud run jobs run django-q-cluster --region us-central1
```

Or call the REST endpoint:

```python
import requests

def run_task_now():
    job_url = f"https://run.googleapis.com/v2/projects/{PROJECT_ID}/locations/us-central1/jobs/django-q-cluster/run"
    requests.post(job_url, headers={"Authorization": f"Bearer {get_token()}"})
```

---

## 8. Limitations

- Django Tasks uses the Django database as a queue — if your DB is slow, task processing is slow.
- No built-in web UI for monitoring (unlike Celery's Flower). Query task status via Django admin.
- **Option B only:** Cloud Run Jobs have a max execution time of 10 minutes (up to 60 configurable). Design long-running tasks accordingly.
- If you need sub-second task dispatch, Django Tasks is not the right choice.

---

## 9. Quick Comparison

| | Option A: Embedded | Option B: Cloud Run Job |
|---|---|---|
| Extra cost | $0 | ~$20–30/month |
| Task latency | Instant (background thread) | Up to 60s |
| Isolation | Shares resources with web | Separate |
| Web can scale to zero | No (min-instances=1) | Yes |
| Cold starts | None (always warm) | Every trigger |
| Complexity | Low | Medium |

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
- 13 — Bonus: Django Tasks (Current chapter)