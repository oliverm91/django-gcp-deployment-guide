---
description: "Añade Cloud Tasks como runner de tareas en segundo plano para Django — escala a cero, sin poll de BD, ~$0/mes."
image: assets/social-banner.png
---
# 13.A — Cloud Tasks via HTTP (Recomendado)

← [Anterior: 13 — Bonus: Django Tasks](13_django_tasks.es.md) | [Siguiente: 13.B — db_worker embebido](13_django_tasks_embedded.es.md) →

Cloud Tasks es el servicio de cola de tareas gestionado de Google. Mantiene la cola y entrega las tareas directamente a tu app via webhook HTTP. Esto te da escala a cero, reintentos con backoff integrados y ningún poll de base de datos — Cloud Run puede apagarse completamente cuando está inactivo y despertar cuando llega una tarea.

Cloud Tasks otorga **1 M operaciones/mes gratis**, luego $0.40/M — a volúmenes típicos es prácticamente gratis.

---

## Paso 1: Habilitar Cloud Tasks y crear la cola

```bash
# Habilitar la API de Cloud Tasks
gcloud services enable cloudtasks.googleapis.com

# Crear una cuenta de servicio dedicada
gcloud iam service-accounts create mycoolproject-cloud-tasks-sa \
  --display-name="MyCoolProject Cloud Tasks SA"

gcloud projects add-iam-policy-binding mycoolproject-prod \
  --member="serviceAccount:mycoolproject-cloud-tasks-sa@mycoolproject-prod.iam.gserviceaccount.com" \
  --role="roles/cloudtasks.queueAdmin"

# Crear la cola en la misma región
gcloud tasks queues create mycoolproject-queue \
  --location=southamerica-east1
```

Otorgar a la SA de Cloud Tasks permiso para llamar a tu servicio de Cloud Run:

```bash
gcloud run services add-iam-policy-binding mycoolproject \
  --region=southamerica-east1 \
  --member="serviceAccount:mycoolproject-cloud-tasks-sa@mycoolproject-prod.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

---

## Paso 2: Agregar el endpoint de despacho de tareas

Dado que no existe aún un paquete de backend Cloud Tasks para `django.tasks`, usa un webhook HTTP manual. Agrega esto a `urls.py`:

```python
# web/core/urls.py
from django.urls import path
from django.http import HttpResponse
import json

def task_webhook(request):
    """Recibe payloads de tareas de Cloud Tasks y las despacha."""
    from .tasks import send_welcome_email  # importa todas las funciones de tarea

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

> **Nota de seguridad:** Solo la cuenta de servicio `mycoolproject-cloud-tasks-sa` puede llamar a este endpoint — el binding IAM `--role=roles/run.invoker` significa que las solicitudes no autenticadas son rechazadas. Cloud Tasks firma cada solicitud HTTP con un token OIDC; Cloud Run lo verifica automáticamente.

---

## Paso 3: Agregar google-cloud-tasks y configurar ImmediateBackend

```bash
cd web
uv add google-cloud-tasks
```

En `prod.py`, usa `ImmediateBackend`:

```python
TASKS = {
    "default": {
        "BACKEND": "django.tasks.backends.immediate.ImmediateBackend",
    },
}
```

**¿Por qué `ImmediateBackend`?** Este backend ejecuta tareas sincrónicamente en el hilo que lo llama — suena como lo opuesto a lo que necesitas, pero es la elección correcta aquí. Con `ImmediateBackend`, llamar a `send_welcome_email()` normalmente ejecuta la tarea inmediatamente. Luego nuestro override de `.enqueue()` intercepta esa llamada y hace POST a Cloud Tasks en su lugar. Cloud Tasks la entrega al webhook más tarde. El resultado: el encolado es instantáneo (sin escritura a BD), la tarea se ejecuta de forma asíncrona via el webhook, y ningún proceso `db_worker` es necesario en absoluto.

Si más tarde cambias a `DatabaseBackend`, llamar a `.enqueue()` escribe directamente a la base de datos — tu código de tarea queda idéntico. Ese es el diseño de backend conectable: cambia el backend, no las tareas.

---

## Paso 4: Crear el helper de Cloud Tasks

Almacena la configuración en variables de entorno (inyectadas desde Secret Manager al arrancar el contenedor) en lugar de hardcodear valores:

```python
# web/mycoolproject/cloud_tasks_helpers.py
"""Encolar funciones estilo django.tasks via la API REST de Cloud Tasks."""

from google.cloud import tasks_v2
import json
import os

PROJECT = os.environ["GCP_PROJECT_ID"]
QUEUE = os.environ["CLOUD_TASKS_QUEUE"]
REGION = os.environ["GCP_REGION"]
SERVICE_URL = os.environ["CLOUD_TASKS_SERVICE_URL"]  # ej. https://mycoolproject.cl
SERVICE_ACCOUNT = os.environ["CLOUD_TASKS_SA_EMAIL"]   # ej. mycoolproject-cloud-tasks-sa@...


def enqueue_task(func, *args, **kwargs):
    """POST una tarea a Cloud Tasks, que la entrega como HTTP a tu servicio."""
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

Inyecta estos cuatro valores al arrancar el contenedor para que diferan entre staging y producción si es necesario:

```bash
gcloud run services update mycoolproject \
  --region=southamerica-east1 \
  --set-secrets=GCP_PROJECT_ID=GCP_PROJECT_ID:latest,CLOUD_TASKS_QUEUE=CLOUD_TASKS_QUEUE:latest,CLOUD_TASKS_SERVICE_URL=CLOUD_TASKS_SERVICE_URL:latest,CLOUD_TASKS_SA_EMAIL=CLOUD_TASKS_SA_EMAIL:latest
```

---

## Paso 5: Conectar el override en tu archivo de tareas

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
        subject="¡Bienvenido a MyCoolProject!",
        message=f"Hola {user.first_name}, ¡bienvenido a bordo!",
        from_email="noreply@mycoolproject.cl",
        recipient_list=[user.email],
        fail_silently=False,
    )


# Sobrescribir .enqueue() para ir via Cloud Tasks en lugar de la BD
_orig_enqueue = send_welcome_email.enqueue
def _cloud_enqueue(*args, **kwargs):
    enqueue_task(send_welcome_email, *args, **kwargs)
send_welcome_email.enqueue = _cloud_enqueue
```

Llámalo igual — `send_welcome_email.enqueue(user.id)` POST a Cloud Tasks, que lo entrega como HTTP POST a tu servicio. Escalado a cero mantenido.

---

## 📖 Navegación

- [13 — Bonus: Django Tasks](13_django_tasks.es.md)
- [13.A — Cloud Tasks via HTTP (Actual)](13_django_tasks_cloud_tasks.es.md)
- [13.B — db_worker embebido](13_django_tasks_embedded.es.md)