---
description: "Add background job processing to Django 6.0 using the built-in django.tasks framework — two worker options: Cloud Tasks via HTTP (recommended) or embedded db_worker."
image: assets/social-banner.png
---
# 13 — Bonus: Django Tasks

← [Previous: 12 — Bonus: Custom Email](12_custom_email.md)

Most Django apps eventually need to run code **outside** the request-response cycle: sending emails, generating reports, processing images, cleaning up old data. These are background jobs.

---

## 1. How a task queue works at a high level

A task queue has three moving parts that must all be present for background work to happen:

**1. Enqueue** — somewhere in your code (a view, a signal, a management command), you call `send_email.enqueue(user.id)`. This serialises the function name + arguments and stores them in a queue. The call returns immediately — the request that triggered it is not blocked.

**2. A queue** — the queue holds pending tasks until a worker is ready to pick them up. It can be your PostgreSQL database (DatabaseBackend), a managed service like Cloud Tasks, or a message broker like Redis or RabbitMQ. Without a queue, tasks just accumulate in memory and vanish when the process exits.

**3. A worker** — a separate process (or thread inside your web process) that constantly polls the queue for new tasks. When it finds one, it deserialises the function + arguments and calls the real Python function. It then marks the task as done or schedules a retry on failure.

```
your code calls send_email.enqueue(user.id)
    → task (function name + args) is serialised and written to the queue
    → your code returns immediately

worker is polling the queue every second
    → picks up the task
    → calls send_email(user.id)
    → marks task complete
```

The worker is the critical piece — without it running anywhere, tasks pile up and never execute. The worker is what this chapter configures in two different ways.

---

## 2. Django Tasks in Django 6.0

Django 6.0 ships `django.tasks` in core (DEP-0014) — a pluggable task queue framework. It provides the `@task()` decorator, the `.enqueue()` call, and the worker command (`db_worker`), but **it does not provide the queue itself**. That is the role of the **backend**.

### Backends

A backend is the piece that connects Django Tasks to a specific queue technology:

| Backend | What it uses as the queue | Who provides it |
|---|---|---|
| `ImmediateBackend` | Nothing — runs tasks synchronously in the current thread | Ships with Django (dev only) |
| `DummyBackend` | Nothing — accepts and drops tasks silently | Ships with Django (testing only) |
| `DatabaseBackend` | Your existing PostgreSQL database (`django_tasks_task` table) | Ships with Django |
| Cloud Tasks backend | Google Cloud Tasks (a managed GCP service) | Third-party package |
| Redis/Celery backend | Redis or RabbitMQ | Third-party package |

Django ships two backends for local use. For production you pick a backend that matches your infrastructure. This chapter compares two options: **`Cloud Tasks via HTTP`** (recommended) and the **`DatabaseBackend` with embedded worker**.

### django.tasks (core) vs. Celery

The comparison is really between `django.tasks` with a lightweight backend vs. a full Celery + message-broker setup:

| Feature | django.tasks + DatabaseBackend | Celery + Redis/RabbitMQ |
|---|---|---|
| Setup complexity | Low — no extra services | High — needs a message broker + separate worker process |
| Infrastructure cost | Zero (co-hosts with Cloud SQL) | High (Redis/RabbitMQ server + runner VM/container) |
| Backend choice | Pluggable — swap backends without touching task code | Celery-specific only |
| Monitoring | Via Django admin | Flower, detailed dashboards |
| Scalability | Fine for low-to-medium volume | Production-grade, handles millions |

**Use django.tasks when:** you have simple jobs (send email, generate PDF, crawl a page), moderate traffic, and want minimal infrastructure.

**Use Celery when:** you have heavy workloads, complex chains/orchestration, or need guarantees that every job is processed even under extreme load.

For a Django app on Cloud Run with Cloud SQL already running, the `DatabaseBackend` is the pragmatic starting point. As traffic grows, swap the backend to a managed queue like Cloud Tasks or a Redis instance without changing a single line of task code.

---

## 3. Configure Django

In `settings/prod.py`:

```python
INSTALLED_APPS += ["django.tasks"]

TASKS = {
    "default": {
        "BACKEND": "django.tasks.backends.database.DatabaseBackend",
        "CRONTAB": "*",  # poll every second — adjust to your volume
    },
}
```

> **Note on DB load:** With `CRONTAB = "*"` (default), the worker polls the database roughly every second. On `db-f1-micro` this keeps one connection busy continuously. For a small app this is acceptable. If you hit DB capacity limits, reduce the poll frequency (e.g. `"*/5"` for every 5 seconds) or move to a dedicated message broker (Redis, Cloud Tasks via HTTP).

---

## 4. Write tasks

```python
# web/mycoolproject/tasks.py
from django.tasks import task

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
```

Call it from anywhere in your code:

```python
# In a view, service, or signal
from .tasks import send_welcome_email

send_welcome_email.enqueue(user.id)
# .enqueue() saves the task to the DB and returns immediately.
# The db_worker polls for due tasks and executes them in the background.
```

### Scheduled (delayed) tasks

```python
from django.tasks import schedule
from datetime import timedelta

# Run 1 hour from now
schedule("mycoolproject.tasks.send_welcome_email", args=[user.id], delay=timedelta(hours=1))
```

---

## 5. Choose your worker option

Both options are production-ready. Pick based on your budget and scaling needs:

| | Option A: Cloud Tasks HTTP | Option B: Embedded db_worker |
|---|---|---|
| Extra cost | ~$0 (within free tier) | ~$10–20/month (always-warm instance) |
| Scale to zero | Yes | No |
| Task latency | Seconds | Seconds |
| DB load | None | One connection 24/7 |
| Setup complexity | Medium | Low |
| Production-ready | Yes (with IAM locked down) | Yes |

**Recommendation:** Start with **Option A (Cloud Tasks)** — it has no extra cost, scale-to-zero means you pay nothing when traffic is zero, and Cloud Tasks handles retries with backoff automatically. Option B is a valid fallback if you prefer to keep everything in one container without any external service dependency.

---

## 6. Limitations

- **`DatabaseBackend`** (Option B) keeps one DB connection busy 24/7. Monitor `db-f1-micro` connection usage.
- Tasks in the database table are picked up by **one worker per instance**. With multiple Cloud Run instances, each polls independently — tasks may run more than once if not idempotent. Use `--max-instances=1` on Cloud Run if exactly-once execution matters.
- Cloud Tasks **Option A** payload limit: **100 KB** per task. Pass IDs, fetch objects inside the handler.
- Handler in Option A must be **idempotent** — Cloud Tasks delivers at-least-once.
- No official `django.tasks` Cloud Tasks backend package exists yet as a stable package. The HTTP integration in Option A is a manual workaround until a third-party backend is available. Check [djangoproject.com/en/6.0/topics/tasks](https://docs.djangoproject.com/en/6.0/topics/tasks) for the current list of third-party backends.

---

## 7. Implementation

Choose your worker option:

- **[13.A — Cloud Tasks via HTTP (Recommended)](13_django_tasks_cloud_tasks.md)** — scale-to-zero, no DB polling, ~$0/month
- **[13.B — Embedded db_worker (Alternative)](13_django_tasks_embedded.md)** — simpler setup, requires always-warm instance

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
- 13 — Bonus: Django Tasks (Overview) *(current chapter)*
  - [13.A — Cloud Tasks via HTTP](13_django_tasks_cloud_tasks.md)
  - [13.B — Embedded db_worker](13_django_tasks_embedded.md)