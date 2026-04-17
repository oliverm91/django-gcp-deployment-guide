---
description: "Añade procesamiento de tareas en segundo plano a Django usando Django Tasks — con dos opciones de runner: embebido o Cloud Run Job separado."
image: assets/social-banner.png
---
# 13 — Bonus: Django Tasks

← [Anterior: 12 — Bonus: Email Personalizado](12_custom_email.es.md)

La mayoría de las aplicaciones Django eventualmente necesitan ejecutar código **fuera** del ciclo request-response: enviar correos, generar informes, procesar imágenes, limpiar datos antiguos. Estas son tareas en segundo plano (background jobs).

---

## 1. Django Tasks

[Django Tasks](https://django-q2.readthedocs.io/) es una cola de tareas ligera construida sobre el propio ORM de Django. No es tan poderosa como Celery, pero es **suficiente para aproximadamente el 80% de las aplicaciones** y requiere mucha menos infraestructura.

### Django Tasks vs. Celery

| Característica | Django Tasks | Celery |
|---|---|---|
| Complejidad de configuración | Baja (solo otra app de Django) | Alta (necesita Redis/RabbitMQ + workers) |
| Confiabilidad | Buena para volumen bajo-medio | Grado producción, maneja millones |
| Monitoreo | Básico | Flower, dashboards detallados |
| Costo de infraestructura | Bajo | Alto (necesita broker + runner) |

**Usa Django Tasks cuando:** tienes tareas simples (enviar email, generar PDF), tráfico moderado, y no quieres gestionar infraestructura extra.

**Usa Celery cuando:** tienes cargas pesadas, encadenamiento complejo, o necesitas garantías de que cada tarea se procese bajo carga extrema.

Para la mayoría de proyectos laterales Django e incluso startups pequeñas, Django Tasks es la elección pragmática.

---

## 2. Instalación y Configuración

```bash
uv add django-q2
```

En tu `settings/prod.py`:

```python
# Configuración de Q_CLUSTER
Q_CLUSTER = {
    "name": "mycoolproject",
    "workers": 4,
    "timeout": 60,
    "orm": "default",  # Usa el ORM de Django como backend de cola
}

# Opcional: reintentar en caso de fallo
Q_CLUSTER["reconnect"] = 10  # segundos
```

Eso es todo — Django Tasks almacena las tareas en tu base de datos PostgreSQL existente. No necesitas Redis.

---

## 3. Escribiendo Tareas

Crea un archivo como `mycoolproject/tasks.py`:

```python
from django_q import task

@task()
def send_welcome_email(user_id):
    from users.models import User
    from django.core.mail import send_mail

    user = User.objects.get(id=user_id)
    send_mail(
        subject="¡Bienvenido a MyCoolProject!",
        message=f"Hola {user.first_name}, ¡bienvenido a bordo!",
        from_email="noreply@mycoolproject.cl",
        recipient_list=[user.email],
    )
```

Llámala desde cualquier parte de tu código:

```python
from .tasks import send_welcome_email

# Fire and forget — retorna inmediatamente, se ejecuta en segundo plano
send_welcome_email(user.id)
```

### Programar tareas recurrentes

En `django_q.py` o `management/commands/`:

```python
from django_q import schedule

# Ejecutar cada hora
schedule("mycoolproject.tasks.cleanup_old_sessions", schedule_type="H")

# Ejecutar todos los días a las 3am
schedule("mycoolproject.tasks.generate_daily_report", schedule_type="D", time=3)
```

---

## 4. Opciones de Runner

Django Tasks necesita un **proceso runner** ejecutándose para recoger y procesar las tareas en cola. Sin él, las tareas se acumulan y nunca se ejecutan. Hay dos enfoques:

### Opción A: Embebido en tu Servicio Web (Recomendado — Gratis)

Ejecuta qcluster como un hilo en segundo plano **dentro de tu contenedor de servicio web existente**. Como tu Cloud Run ya corre con `min_instances=1` (siempre activo), el runner no cuesta nada extra.

| | |
|---|---|
| **Pros** | Costo adicional cero. Sin infraestructura extra. Las tareas se procesan al instante. |
| **Cons** | El runner comparte CPU/memoria con las peticiones web. Tareas pesadas pueden afectar los tiempos de respuesta. Si el servicio web se reinicia, qcluster también lo hace. |

### Opción B: Cloud Run Job Separado

Despliega qcluster como un **Cloud Run Job separado** disparado por Cloud Scheduler cada minuto.

| | |
|---|---|
| **Pros** |aislado del servicio web — tareas pesadas no afectan la latencia de requests. El servicio web puede escalar a cero independientemente. |
| **Cons** | Caro: ~$20–30/mes por los frecuentes cold starts (1440 disparos/día). Latencia de hasta 60s antes de que se ejecuten las tareas. Más infraestructura que gestionar. |

**Recomendación:** Empieza con la Opción A. Actualiza a la Opción B solo si tu carga de tareas crece hasta interferir con el rendimiento web.

---

## 5. Opción A: Runner Embebido (Implementación)

Como tu servicio Cloud Run está siempre activo (`min_instances=1`), ejecuta qcluster en el mismo contenedor como un proceso en segundo plano.

### Modifica tu entrypoint

Crea un script de inicio personalizado que lance tanto gunicorn como qcluster:

```bash
#!/bin/bash
# start.sh — ejecuta gunicorn (web) y qcluster (runner de tareas) juntos

# Iniciar qcluster en segundo plano
python manage.py qcluster &
QCLUSTER_PID=$!

# Iniciar gunicorn (espera a que termine)
exec gunicorn core.wsgi:application \
    --bind 0.0.0.0:8080 \
    --workers 2 \
    --threads 4 \
    --timeout 60 \
    --log-file -
```

Hazlo ejecutable:

```bash
chmod +x start.sh
```

### Actualiza tu Dockerfile

Modifica tu `Dockerfile` para usar el entrypoint personalizado:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Usar script de inicio personalizado en vez de ejecutar gunicorn directamente
CMD ["./start.sh"]
```

### Actualiza la configuración de Cloud Run

Asegúrate de que tu servicio web tenga `min-instances=1` para que qcluster permanezca activo:

```bash
gcloud run services update mycoolproject \
    --region=southamerica-east1 \
    --min-instances=1
```

Eso es todo. En cada despliegue del servicio web, qcluster inicia automáticamente junto con gunicorn y procesa las tareas cuando llegan. Sin recursos Cloud Run adicionales, sin Cloud Scheduler, sin costo extra.

---

## 6. Opción B: Cloud Run Job Separado

Si necesitas aislamiento (cargas de tareas pesadas) o quieres que tu servicio web escale a cero independientemente, usa un Cloud Run Job separado.

### Paso 1: Crear una cuenta de servicio separada

```bash
gcloud iam service-accounts create django-q-runner \
    --display-name="Django Q Runner"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:django-q-runner@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"
```

### Paso 2: Construir una imagen Docker para jobs

Crea `Dockerfile.job`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "manage.py", "qcluster"]
```

Construir y subir:

```bash
gcloud builds submit \
    --tag gcr.io/$PROJECT_ID/mycoolproject-job:v1 \
    --dockerfile Dockerfile.job
```

### Paso 3: Crear el Cloud Run Job

```bash
gcloud run jobs create django-q-cluster \
    --image gcr.io/$PROJECT_ID/mycoolproject-job:v1 \
    --service-account django-q-runner@$PROJECT_ID.iam.gserviceaccount.com \
    --region us-central1 \
    --max-retries 2
```

### Paso 4: Programar el job cada minuto

Cloud Run Jobs no tiene cron integrado — usa Cloud Scheduler:

```bash
gcloud scheduler jobs create http django-q-trigger \
    --schedule="* * * * *" \
    --uri=https://run.googleapis.com/v2/projects/$PROJECT_ID/locations/us-central1/jobs/django-q-cluster/run \
    --http-method POST \
    --oauth-service-account-email django-q-runner@$PROJECT_ID.iam.gserviceaccount.com
```

> 💡 **¿Por qué cada minuto?** Django Tasks almacena las tareas programadas con un `next_run_time`. El runner solo procesa las tareas que están pendientes. Ejecutar cada minuto es barato y suficientemente receptivo.

**Advertencia de costo:** Esto dispara ~43,200/mes, costando ~$20–30/mes. Considera la Opción A en su lugar.

---

## 7. Ejecutar Tareas Inmediatamente (On-Demand)

### Opción A (runner embebido)

Las tareas se ejecutan inmediatamente cuando se encolan — no necesitas paso extra:

```python
send_welcome_email(user.id)  # se ejecuta en segundos
```

Para forzar una ejecución inmediata de tareas programadas:

```bash
# Ejecuta dentro del contenedor en ejecución (sin nuevo despliegue)
gcloud run exec -it mycoolproject --region=southamerica-east1 -- python manage.py qcluster
```

### Opción B (Cloud Run Job)

Dispara el job manualmente:

```bash
gcloud run jobs run django-q-cluster --region us-central1
```

O llama al endpoint REST:

```python
import requests

def run_task_now():
    job_url = f"https://run.googleapis.com/v2/projects/{PROJECT_ID}/locations/us-central1/jobs/django-q-cluster/run"
    requests.post(job_url, headers={"Authorization": f"Bearer {get_token()}"})
```

---

## 8. Limitaciones

- Django Tasks usa la base de datos de Django como cola — si tu DB es lenta, el procesamiento de tareas es lento.
- No tiene interfaz web integrada para monitoreo (a diferencia de Flower de Celery). Consulta el estado vía el admin de Django.
- **Solo Opción B:** Cloud Run Jobs tienen un tiempo máximo de ejecución de 10 minutos (configurable hasta 60). Diseña tareas largas accordingly.
- Si necesitas despacho de tareas en menos de un segundo, Django Tasks no es la elección correcta.

---

## 9. Comparación Rápida

| | Opción A: Embebido | Opción B: Cloud Run Job |
|---|---|---|
| Costo adicional | $0 | ~$20–30/mes |
| Latencia de tareas | Instantáneo (hilo en background) | Hasta 60s |
| Aislamiento | Comparte recursos con web | Separado |
| Web puede escalar a cero | No (min-instances=1) | Sí |
| Cold starts | Ninguno (siempre activo) | Cada disparo |
| Complejidad | Baja | Media |

---

## 📖 Navegación

- [01 — Configuración del Proyecto GCP](01_gcp_setup.es.md)
- [02 — Artifact Registry](02_artifact_registry.es.md)
- [03 — Cloud SQL (Base de datos PostgreSQL)](03_cloud_sql.es.md)
- [04 — Secret Manager](04_secret_manager.es.md)
- [05 — Cloud Storage (Media & Static Files)](05_cloud_storage.es.md)
- [06 — Dockerfile](06_dockerfile.es.md)
- [07 — Primer Despliegue](07_first_deploy.es.md)
- [08 — Dominio Personalizado y SSL](08_domain_ssl.es.md)
- [09 — Workload Identity Federation (Auth de GitHub sin llaves)](09_workload_identity.es.md)
- [10 — Pipeline CI/CD con GitHub Actions](10_github_actions.es.md)
- [11 — Referencia Rápida](11_quick_reference.es.md)
- [12 — Bonus: Email Personalizado (@dominio.cl)](12_custom_email.es.md)
- 13 — Bonus: Django Tasks (Capítulo actual)