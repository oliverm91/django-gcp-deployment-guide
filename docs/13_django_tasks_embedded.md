---
description: "Run db_worker inside your Cloud Run container — simpler setup, requires always-warm instance."
image: assets/social-banner.png
---
# 13.B — Embedded db_worker (Alternative)

← [Previous: 13 — Bonus: Django Tasks](13_django_tasks.md) | [Next: 13.A — Cloud Tasks via HTTP](13_django_tasks_cloud_tasks.md) →

If you prefer to keep everything in one process without any external service dependency, run the `db_worker` inside your Cloud Run container. Cloud Run wakes the web handler when a request arrives, and the same container's background worker polls the database for tasks.

> **Cost note:** this option requires `--min-instances=1` + `--no-cpu-throttling` to keep the worker running. This costs roughly **$10–20/month** — not zero. Use [Option A (Cloud Tasks)](13_django_tasks_cloud_tasks.md) if you need scale-to-zero.

---

## Step 1: Update the start script

Create `start.sh` at the project root:

```bash
#!/bin/bash
# start.sh — run both gunicorn (web) and db_worker (task runner) together.
# Using trap ensures both processes receive SIGTERM gracefully on container shutdown.

# Start db_worker in background
python manage.py db_worker &
DB_WORKER_PID=$!

# Trap SIGTERM and forward it to both processes
trap "kill -TERM $DB_WORKER_PID; wait $DB_WORKER_PID" SIGTERM

# Start gunicorn as PID 1 (exec ensures it's PID 1 — Cloud Run's SIGTERM reaches it cleanly)
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

---

## Step 2: Update the Dockerfile

```dockerfile
# ... existing Dockerfile content ...

# Use custom start script
CMD ["./start.sh"]
```

---

## Step 3: Update the Cloud Run service

The worker needs CPU allocated continuously (not throttled between requests):

```bash
gcloud run services update mycoolproject \
  --region=southamerica-east1 \
  --no-cpu-throttling \
  --min-instances=1
```

> **CPU throttling explained:** by default, Cloud Run only allocates CPU during request processing. When idle, CPU is throttled to zero. The `db_worker` polls the database every second — if CPU is throttled between requests, the polling stops and tasks pile up. `--no-cpu-throttling` keeps the CPU running even when not handling traffic, so the worker can keep polling. This is why `--min-instances=1` is required — the instance must stay warm to keep the worker alive.

---

## Task polling and multiple instances

With `DatabaseBackend`, each Cloud Run instance runs its own `db_worker` that polls the database independently. If you run multiple instances (`--max-instances > 1`), each worker polls simultaneously and the same task may be picked up by more than one instance.

**If exactly-once execution matters** (e.g. sending two emails for one signup): set `--max-instances=1` so only one instance ever runs, guaranteeing the worker picks up each task exactly once.

**If you can tolerate at-least-once** (e.g. image processing that checks "already processed" before running): scale freely — Cloud Tasks handles this with visibility timeout; the embedded worker handles it by marking the task complete before another instance can pick it up.

---

## 📖 Navigation

- [13 — Bonus: Django Tasks](13_django_tasks.md)
- [13.A — Cloud Tasks via HTTP](13_django_tasks_cloud_tasks.md)
- [13.B — Embedded db_worker (Current)](13_django_tasks_embedded.md)