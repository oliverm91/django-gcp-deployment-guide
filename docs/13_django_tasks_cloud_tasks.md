---
description: "Add Cloud Tasks as your Django background job runner — scale-to-zero, no DB polling, ~$0/month."
image: assets/social-banner.png
---
# 13.A — Cloud Tasks via HTTP (Recommended)

← [Previous: 13 — Bonus: Django Tasks](13_django_tasks.md) | [Next: 13.B — Embedded db_worker](13_django_tasks_embedded.md) →

Cloud Tasks is Google's managed task queue service. It holds the queue and delivers tasks directly to your app via an HTTP webhook. This gives you scale-to-zero, built-in retries with backoff, and no database polling — Cloud Run can shut down completely when idle and wake up when a task arrives.

Cloud Tasks provides **1 M operations/month free**, then $0.40/M — at typical volumes effectively free.

---

## Step 1: Enable Cloud Tasks and create the queue

```bash
# Enable the Cloud Tasks API
gcloud services enable cloudtasks.googleapis.com

# Create a dedicated service account
gcloud iam service-accounts create mycoolproject-cloud-tasks-sa \
  --display-name="MyCoolProject Cloud Tasks SA"

gcloud projects add-iam-policy-binding mycoolproject-prod \
  --member="serviceAccount:mycoolproject-cloud-tasks-sa@mycoolproject-prod.iam.gserviceaccount.com" \
  --role="roles/cloudtasks.queueAdmin"

# Create the queue in the same region
gcloud tasks queues create mycoolproject-queue \
  --location=southamerica-east1
```

Grant the Cloud Tasks SA permission to call your Cloud Run service:

```bash
gcloud run services add-iam-policy-binding mycoolproject \
  --region=southamerica-east1 \
  --member="serviceAccount:mycoolproject-cloud-tasks-sa@mycoolproject-prod.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

---

## Step 2: Add the task dispatch endpoint

Since no `django.tasks` Cloud Tasks backend package exists yet, use a manual HTTP webhook to dispatch tasks. Add this to `urls.py`:

```python
# web/core/urls.py
from django.urls import path
from django.http import HttpResponse
import json

def task_webhook(request):
    """Receives task payloads from Cloud Tasks and dispatches them."""
    from .tasks import send_welcome_email  # import all task functions

    task_map = {
        "mycoolproject.tasks.send_welcome_email": send_welcome_email,
    }

    try:
        body = json.loads(request.body)
        func_name = body.get("func")
        args = body.get("args", [])
        kwargs = body.get("kwargs", {})
        func = task_map.get(func_name)
        if func:
            func(*args, **kwargs)
        return HttpResponse("ok")
    except Exception as e:
        return HttpResponse(str(e), status=500)

urlpatterns += [
    path("internal/tasks/run/", task_webhook),
]
```

> **Security note:** Only the `mycoolproject-cloud-tasks-sa` service account can call this endpoint — the `--role=roles/run.invoker` IAM binding means unauthenticated requests are rejected. Cloud Tasks signs each HTTP request with an OIDC token; Cloud Run verifies it automatically.

---

## Step 3: Add google-cloud-tasks and configure ImmediateBackend

```bash
cd web
uv add google-cloud-tasks
```

In `prod.py`, use `ImmediateBackend`:

```python
TASKS = {
    "default": {
        "BACKEND": "django.tasks.backends.immediate.ImmediateBackend",
    },
}
```

**Why `ImmediateBackend`?** It runs tasks synchronously in the calling thread — that sounds like the opposite of what you want, but it's the right choice here. With `ImmediateBackend`, calling `send_welcome_email()` normally runs the task immediately. Then our `.enqueue()` override intercepts that call and POSTs the task to Cloud Tasks instead. Cloud Tasks delivers it to the webhook later. The result: enqueuing is instant (no DB write), the task still runs asynchronously via the webhook, and no background worker process is needed at all.

If you later swap to `DatabaseBackend`, calling `.enqueue()` writes to the database directly — your task code stays identical. That's the pluggable-backend design: swap the backend, not the tasks.

---

## Step 4: Create the Cloud Tasks helper

Store configuration in env vars (injected from Secret Manager at container startup) rather than hardcoding project-specific values:

```python
# web/mycoolproject/cloud_tasks_helpers.py
"""Enqueue django.tasks-style functions via the Cloud Tasks REST API."""

from google.cloud import tasks_v2
import json
import os

PROJECT = os.environ["GCP_PROJECT_ID"]
QUEUE = os.environ["CLOUD_TASKS_QUEUE"]
REGION = os.environ["GCP_REGION"]
SERVICE_URL = os.environ["CLOUD_TASKS_SERVICE_URL"]  # e.g. https://mycoolproject.cl
SERVICE_ACCOUNT = os.environ["CLOUD_TASKS_SA_EMAIL"]   # e.g. mycoolproject-cloud-tasks-sa@...


def enqueue_task(func, *args, **kwargs):
    """POST a task to Cloud Tasks, which delivers it as HTTP to your service."""
    client = tasks_v2.CloudTasksClient()

    task = tasks_v2.Task(
        http_request=tasks_v2.HttpRequest(
            http_method=tasks_v2.HttpMethod.POST,
            url=f"{SERVICE_URL}/internal/tasks/run/",
            headers={"Content-Type": "application/json"},
            body=json.dumps({
                "func": f"{func.__module__}.{func.__name__}",
                "args": args,
                "kwargs": kwargs,
            }).encode(),
            oidc_token=tasks_v2.OidcToken(
                service_account_email=SERVICE_ACCOUNT,
            ),
        )
    )

    queue_path = client.queue_path(PROJECT, REGION, QUEUE)
    client.create_task(parent=queue_path, task=task)
```

Inject these four values at container startup so they differ between staging and production if needed:

```bash
gcloud run services update mycoolproject \
  --region=southamerica-east1 \
  --set-secrets=GCP_PROJECT_ID=GCP_PROJECT_ID:latest,CLOUD_TASKS_QUEUE=CLOUD_TASKS_QUEUE:latest,CLOUD_TASKS_SERVICE_URL=CLOUD_TASKS_SERVICE_URL:latest,CLOUD_TASKS_SA_EMAIL=CLOUD_TASKS_SA_EMAIL:latest
```

---

## Step 5: Wire the override in your tasks file

```python
# web/mycoolproject/tasks.py
from django.tasks import task
from .cloud_tasks_helpers import enqueue_task

@task()
def send_welcome_email(user_id: int) -> None:
    from django.core.mail import send_mail
    from django.contrib.auth import get_user_model

    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return

    send_mail(
        subject="Welcome to MyCoolProject!",
        message=f"Hi {user.first_name}, welcome aboard!",
        from_email="noreply@mycoolproject.cl",
        recipient_list=[user.email],
        fail_silently=False,
    )


# Override .enqueue() to POST to Cloud Tasks instead of running synchronously
_orig_enqueue = send_welcome_email.enqueue
def _cloud_enqueue(*args, **kwargs):
    enqueue_task(send_welcome_email, *args, **kwargs)
send_welcome_email.enqueue = _cloud_enqueue
```

Call it the same way — `send_welcome_email.enqueue(user.id)` POSTs to Cloud Tasks, which delivers it as an HTTP POST to your webhook. Scale to zero maintained.

---

## 📖 Navigation

- [13 — Bonus: Django Tasks](13_django_tasks.md)
- [13.A — Cloud Tasks via HTTP (Current)](13_django_tasks_cloud_tasks.md)
- [13.B — Embedded db_worker](13_django_tasks_embedded.md)