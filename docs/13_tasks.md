---
description: "Create a Cloud Tasks queue and Cloud Scheduler job for background task processing."
image: assets/social-banner.png
---

# 13 — Cloud Tasks & Scheduler

← [Previous: 11 — Cloud Run](12_cloud_run.md)

Cloud Tasks is a managed task queue for background jobs. Cloud Scheduler triggers the worker on a schedule. This chapter creates both with Terraform.

---

## How it fits together

```
Django (web request)
    │
    ├── Enqueues task to Cloud Tasks queue
    │
    └── Responds to user immediately

Cloud Tasks queue
    │
    └── Cloud Scheduler (triggers every minute)
              │
              ▼
         Cloud Run Job (worker)
              │
              └── Pulls tasks from queue
                    │
                    └── Processes them (send email, etc.)
```

---

## Create the Cloud Tasks queue

Add to `infrastructure/main.tf`:

```hcl
# Cloud Tasks queue
resource "google_cloud_tasks_queue" "default" {
  name     = "mycoolproject-default"
  location = var.region

  # Retry configuration (if a task fails, retry it)
  retry_config {
    # Min time between retries
    min_backoff = "10s"
    # Max time between retries
    max_backoff = "600s"
    # Max number of retries
    max_attempts = 5
    # Time limit for task to complete
    max_retry_duration = "600s"
  }

  # Location (region)
  # Stackdriver logs for Cloud Tasks
  route_queue {
  }
}

output "cloud_tasks_queue_name" {
  value = google_cloud_tasks_queue.default.name
}
```

Run `terraform apply` to create the queue.

---

## Create the Cloud Tasks worker (Cloud Run Job)

Cloud Tasks holds tasks, but a Cloud Run Job actually processes them. Add to `main.tf`:

```hcl
# Cloud Run Job for processing Cloud Tasks
resource "google_cloud_run_v2_job" "worker" {
  name     = "mycoolproject-worker"
  location = var.region

  # Which service account the job runs as
  service_account = google_service_account.worker.email

  template {
    # One-time execution (not a continuous service)
    launch_stage = "GA"

    template {
      spec {
        service_account = google_service_account.worker.email

        containers {
          image = "${google_artifact_registry_repository.app.repository_url}/app:latest"
          command = ["uv", "run", "django_q", "cluster"]
          args = []
        }

        # Resource limits
        resources {
          limits {
            cpu    = "1"
            memory = "512Mi"
          }
        }

        # Timeout for the entire job
        timeout = "3600s"

        # Max instances (prevent runaway)
        max_instance_count = 3
      }

      # Region
      annotations = {
        "cloud.google.com/location" = var.region
      }
    }
  }

  # Ingress settings (allow internal only)
  ingress = "INGRESS_TRAFFIC_ALL"
}

# Make the job callable (allow Cloud Scheduler to trigger it)
resource "google_cloud_run_v2_job_iam_member" "worker_invoker" {
  location = google_cloud_run_v2_job.worker.location
  name     = google_cloud_run_v2_job.worker.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scheduler.email}"
}

output "worker_job_name" {
  value = google_cloud_run_v2_job.worker.name
}
```

---

## Cloud Scheduler to trigger the worker

Add to `main.tf`:

```hcl
# Service account for Cloud Scheduler
resource "google_service_account" "scheduler" {
  account_id   = "mycoolproject-scheduler"
  display_name = "MyCoolProject Scheduler Service Account"
}

# Grant permission to invoke Cloud Run Jobs
resource "google_project_iam_member" "scheduler_cloud_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.scheduler.email}"
}

# Cloud Scheduler job - triggers worker every minute
resource "google_cloud_scheduler_job" "worker_trigger" {
  name        = "mycoolproject-worker-trigger"
  description = "Trigger the Cloud Tasks worker every minute"
  region      = var.region
  schedule    = "* * * * *"  # Every minute (cron format)

  # Trigger a Cloud Run Job
  http_target {
    uri         = "https://${var.region}-run.googleapis.com/v2/projects/${var.project_id}/locations/${var.region}/jobs/${google_cloud_run_v2_job.worker.name}:run"
    http_method = "POST"

    # Authenticate using the scheduler service account
    oidc_token {
      service_account_email = google_service_account.scheduler.email
    }
  }

  # Retry config
  retry_config {
    min_backoff_duration  = "10s"
    max_backoff_duration  = "60s"
    max_retry_duration    = "60s"
    retry_count           = 3
  }

  time_zone = "UTC"
}

output "scheduler_job_name" {
  value = google_cloud_scheduler_job.worker_trigger.name
}
```

Run `terraform apply` to create the scheduler job.

---

## The cron schedule format

`* * * * *` means "every minute." The format is:

```
┌───────────── minute (0-59)
│ ┌───────────── hour (0-23)
│ │ ┌───────────── day of month (1-31)
│ │ │ ┌───────────── month (1-12)
│ │ │ │ ┌───────────── day of week (0-6, Sunday=0)
│ │ │ │ │
* * * * *
```

Common schedules:

| Schedule | Meaning |
|---|---|
| `* * * * *` | Every minute |
| `0 * * * *` | Every hour at minute 0 |
| `0 9 * * *` | Every day at 9am |
| `0 9 * * 1-5` | Weekdays at 9am |
| `*/15 * * * *` | Every 15 minutes |

---

## How Django enqueues tasks

Django uses Google Cloud Tasks client library to enqueue tasks:

```python
from google.cloud import tasks_v2
import os

def send_welcome_email(user_id):
    client = tasks_v2.CloudTasksClient()
    queue_name = f"projects/{os.environ['GCP_PROJECT']}/locations/{os.environ['GCP_REGION']}/queues/mycoolproject-default"

    task = {
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": f"{os.environ['APP_URL']}/tasks/send-email/",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"user_id": user_id}).encode(),
        }
    }

    client.create_task(request={"parent": queue_name, "task": task})
```

The task points to a URL on your Django app. The worker (Cloud Run Job) runs `django_q cluster` which polls the queue and processes tasks.

---

## Alternative: Use Django-Q directly

Django-Q (django-q2) is a task queue library built on Django's ORM. It can use Cloud Tasks as its broker instead of the Django database:

```python
# In settings/prod.py
Q_CLUSTER = {
    "name": "mycoolproject",
    "workers": 4,
    "timeout": 60,
    "broker": "cloudtasks",  # Use Cloud Tasks instead of database
    "project": os.environ["GCP_PROJECT"],
    "location": os.environ["GCP_REGION"],
    "queue": "mycoolproject-default",
}
```

This is simpler than the HTTP approach above — Django-Q handles the Cloud Tasks API directly.

---

## Summary: what we created

- Cloud Tasks queue (`mycoolproject-default`)
- Cloud Run Job for worker (`mycoolproject-worker`)
- Cloud Scheduler job (triggers worker every minute)
- Service accounts and IAM for all three

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
- [09 — Cloud Storage](10_storage.md)
- [10 — Service Accounts & IAM](11_iam.md)
- [11 — Cloud Run](12_cloud_run.md)
- 12 — Cloud Tasks & Scheduler (Current chapter)
- [13 — Dockerfile](14_dockerfile.md)
- [14 — First Deploy](15_first_deploy.md)
- [15 — Custom Domain & SSL](16_domain_ssl.md)
- [16 — Workload Identity Federation](17_wif.md)
- [17 — GitHub Actions CI/CD](18_github_actions.md)
- [18 — Quick Reference](19_quick_reference.md)