---
description: "Crea una cola de Cloud Tasks y un job de Cloud Scheduler para procesamiento de tareas en segundo plano."
image: assets/social-banner.png
---

# 12 — Cloud Tasks y Scheduler

← [Anterior: 11 — Cloud Run](12_cloud_run.es.md)

Cloud Tasks es una cola de tareas gestionada para trabajos en segundo plano. Cloud Scheduler activa el worker en un horario. Este capítulo crea ambos con Terraform.

---

## Cómo encajan juntos

```
Django (solicitud web)
    │
    ├── Encola tarea a la cola de Cloud Tasks
    │
    └── Responde al usuario inmediatamente

Cola de Cloud Tasks
    │
    └── Cloud Scheduler (activa cada minuto)
              │
              ▼
         Cloud Run Job (worker)
              │
              └── Extrae tareas de la cola
                    │
                    └── Las procesa (enviar email, etc.)
```

---

## Crear la cola de Cloud Tasks

Agrega a `infrastructure/main.tf`:

```hcl
# Cloud Tasks queue
resource "google_cloud_tasks_queue" "default" {
  name     = "mycoolproject-default"
  location = var.region

  # Retry configuration (if a task fails, retry it)
  retry_config {
    min_backoff = "10s"
    max_backoff = "600s"
    max_attempts = 5
    max_retry_duration = "600s"
  }
}

output "cloud_tasks_queue_name" {
  value = google_cloud_tasks_queue.default.name
}
```

Ejecuta `terraform apply` para crear la cola.

---

## Crear el worker de Cloud Tasks (Cloud Run Job)

Cloud Tasks contiene tareas, pero un Cloud Run Job realmente las procesa. Agrega a `main.tf`:

```hcl
# Cloud Run Job for processing Cloud Tasks
resource "google_cloud_run_v2_job" "worker" {
  name     = "mycoolproject-worker"
  location = var.region

  service_account = google_service_account.worker.email

  template {
    launch_stage = "GA"

    template {
      spec {
        service_account = google_service_account.worker.email

        containers {
          image = "${google_artifact_registry_repository.app.repository_url}/app:latest"
          command = ["uv", "run", "django_q", "cluster"]
          args = []
        }

        resources {
          limits {
            cpu    = "1"
            memory = "512Mi"
          }
        }

        timeout = "3600s"
        max_instance_count = 3
      }

      annotations = {
        "cloud.google.com/location" = var.region
      }
    }
  }

  ingress = "INGRESS_TRAFFIC_ALL"
}

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

## Cloud Scheduler para activar el worker

Agrega a `main.tf`:

```hcl
# Service account for Cloud Scheduler
resource "google_service_account" "scheduler" {
  account_id   = "mycoolproject-scheduler"
  display_name = "MyCoolProject Scheduler Service Account"
}

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
  schedule    = "* * * * *"

  http_target {
    uri         = "https://${var.region}-run.googleapis.com/v2/projects/${var.project_id}/locations/${var.region}/jobs/${google_cloud_run_v2_job.worker.name}:run"
    http_method = "POST"

    oidc_token {
      service_account_email = google_service_account.scheduler.email
    }
  }

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

Ejecuta `terraform apply` para crear el job del scheduler.

---

## El formato de horario cron

`* * * * *` significa "cada minuto." El formato es:

```
┌───────────── minuto (0-59)
│ ┌───────────── hora (0-23)
│ │ ┌───────────── día del mes (1-31)
│ │ │ ┌───────────── mes (1-12)
│ │ │ │ ┌───────────── día de la semana (0-6, Domingo=0)
│ │ │ │ │
* * * * *
```

Horarios comunes:

| Horario | Significado |
|---|---|
| `* * * * *` | Cada minuto |
| `0 * * * *` | Cada hora en el minuto 0 |
| `0 9 * * *` | Cada día a las 9am |
| `0 9 * * 1-5` | Entre semana a las 9am |
| `*/15 * * * *` | Cada 15 minutos |

---

## Cómo Django encola tareas

Django usa la librería cliente de Google Cloud Tasks para encolar tareas:

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

La tarea apunta a una URL en tu app Django. El worker (Cloud Run Job) ejecuta `django_q cluster` que sondea la cola y procesa tareas.

---

## Alternativa: Usar Django-Q directamente

Django-Q (django-q2) es una librería de cola de tareas construida sobre el ORM de Django. Puede usar Cloud Tasks como su broker en lugar de la base de datos:

```python
# In settings/prod.py
Q_CLUSTER = {
    "name": "mycoolproject",
    "workers": 4,
    "timeout": 60,
    "broker": "cloudtasks",
    "project": os.environ["GCP_PROJECT"],
    "location": os.environ["GCP_REGION"],
    "queue": "mycoolproject-default",
}
```

---

## Resumen: qué creamos

- Cola de Cloud Tasks (`mycoolproject-default`)
- Cloud Run Job para worker (`mycoolproject-worker`)
- Job de Cloud Scheduler (activa worker cada minuto)
- Service accounts e IAM para los tres

---

## Navegación



- [01 — Introducción: Qué vamos a construir](01_introduction.es.md)
- [02 — Visión general de Terraform](02_terraform_overview.es.md)
- [03 — Servicios en la nube explicados](03_cloud_services.es.md)
- [04 — Base de datos PlanetScale explicada](04_planetscale.es.md)
- [05 — Configuración del proyecto y estado de Terraform](05_project_setup.es.md)
- [06 — Proyecto GCP y APIs](06_gcp_project.es.md)
- [07 — Artifact Registry](07_artifact_registry.es.md)
- [08 — Gestión de Secretos](09_secrets.es.md)
- [09 — Cloud Storage](10_storage.es.md)
- [10 — Service Accounts e IAM](11_iam.es.md)
- [11 — Cloud Run](12_cloud_run.es.md)
- 12 — Cloud Tasks y Scheduler (Capítulo actual)
- [13 — Dockerfile](14_dockerfile.es.md)
- [14 — Primer Despliegue](15_first_deploy.es.md)
- [15 — Dominio personalizado y SSL](16_domain_ssl.es.md)
- [16 — Workload Identity Federation](17_wif.es.md)
- [17 — GitHub Actions CI/CD](18_github_actions.es.md)
- [18 — Referencia Rápida](19_quick_reference.es.md)
