---
description: "Añade procesamiento de tareas en segundo plano a Django 6.0 usando el framework django.tasks incorporado — dos opciones: Cloud Tasks via HTTP (recomendado) o db_worker embebido."
image: assets/social-banner.png
---
# 13 — Bonus: Django Tasks

← [Anterior: 12 — Bonus: Email Personalizado](12_custom_email.es.md)

La mayoría de las aplicaciones Django eventualmente necesitan ejecutar código **fuera** del ciclo request-response: enviar correos, generar informes, procesar imágenes, limpiar datos antiguos. Estas son tareas en segundo plano (background jobs).

---

## 1. Cómo funciona una cola de tareas a alto nivel

Una cola de tareas tiene tres componentes que deben estar presentes para que el trabajo en segundo plano funcione:

**1. Encolar** — en algún lugar de tu código (una vista, una señal, un comando de gestión), llamas a `send_email.enqueue(user.id)`. Esto serializa el nombre de la función + argumentos y los almacena en una cola. La llamada retorna inmediatamente — la solicitud que la activó no se bloquea.

**2. Una cola** — la cola mantiene las tareas pendientes hasta que un worker está listo para recogerlas. Puede ser tu base de datos PostgreSQL (DatabaseBackend), un servicio gestionado como Cloud Tasks, o un message broker como Redis o RabbitMQ. Sin una cola, las tareas se acumulan en memoria y desaparecen cuando el proceso termina.

**3. Un worker** — un proceso separado (o hilo dentro de tu proceso web) que constantemente poll la cola buscando tareas nuevas. Cuando encuentra una, deserializa la función + argumentos y llama a la función Python real. Luego marca la tarea como completada o programa un reintento en caso de fallo.

```
tu código llama send_email.enqueue(user.id)
    → tarea (nombre función + args) se serializa y escribe a la cola
    → tu código retorna inmediatamente

worker está poll-eando la cola cada segundo
    → recoge la tarea
    → llama send_email(user.id)
    → marca tarea como completada
```

El worker es la pieza crítica — sin él ejecutándose en algún lugar, las tareas se acumulan y nunca se ejecutan. El worker es lo que este capítulo configura de dos formas diferentes.

---

## 2. Django Tasks en Django 6.0

Django 6.0 incluye `django.tasks` en su núcleo (DEP-0014) — un framework de cola de tareas conectable. Proporciona el decorador `@task()`, la llamada `.enqueue()` y el comando worker (`db_worker`), pero **no proporciona la cola en sí**. Ese es el rol del **backend**.

### Backends

Un backend es la pieza que conecta Django Tasks con una tecnología de cola específica:

| Backend | Lo que usa como cola | Quién lo provee |
|---|---|---|
| `ImmediateBackend` | Nada — ejecuta tareas sincrónicamente en el hilo actual | Incluye Django (solo desarrollo) |
| `DummyBackend` | Nada — acepta y descarta tareas silenciosamente | Incluye Django (solo testing) |
| `DatabaseBackend` | Tu base de datos PostgreSQL existente (tabla `django_tasks_task`) | Incluye Django |
| Backend Cloud Tasks | Google Cloud Tasks (un servicio GCP gestionado) | Paquete de tercero |
| Backend Redis/Celery | Redis o RabbitMQ | Paquete de tercero |

Django incluye dos backends para uso local. Para producción eliges un backend que se ajuste a tu infraestructura. Este capítulo compara dos opciones: **`Cloud Tasks via HTTP`** (recomendado) y el **`DatabaseBackend` con worker embebido**.

### django.tasks (core) vs. Celery

La comparación es realmente entre `django.tasks` con un backend ligero vs. una configuración completa de Celery + message-broker:

| Característica | django.tasks + DatabaseBackend | Celery + Redis/RabbitMQ |
|---|---|---|
| Complejidad de configuración | Baja — sin servicios extra | Alta — necesita message broker + proceso worker separado |
| Costo de infraestructura | Cero (comparte Cloud SQL) | Alto (servidor Redis/RabbitMQ + runner VM/contenedor) |
| Elección de backend | Conectable — cambia backends sin tocar código de tareas | Solo específico de Celery |
| Monitoreo | Vía admin de Django | Flower, dashboards detallados |
| Escalabilidad | Adecuado para volumen bajo-medio | Grado producción, maneja millones |

**Usa django.tasks cuando:** tienes tareas simples (enviar email, generar PDF), tráfico moderado y quieres infraestructura mínima.

**Usa Celery cuando:** tienes cargas pesadas, encadenamiento complejo u necesitas garantías de que cada tarea se procese bajo carga extrema.

Para una app Django en Cloud Run con Cloud SQL ya ejecutándose, el `DatabaseBackend` es el punto de partida pragmático. A medida que el tráfico crece, muda el backend a una cola gestionada como Cloud Tasks o una instancia Redis sin cambiar una sola línea de código de tarea.

---

## 3. Configurar Django

En `settings/prod.py`:

```python
INSTALLED_APPS += ["django.tasks"]

TASKS = {
    "default": {
        "BACKEND": "django.tasks.backends.database.DatabaseBackend",
        "CRONTAB": "*",  # poll cada segundo — ajústalo a tu volumen
    },
}
```

> **Nota sobre carga de BD:** Con `CRONTAB = "*"` (default), el worker poll la base de datos aproximadamente cada segundo. En `db-f1-micro` esto mantiene una conexión ocupada continuamente. Para una app pequeña es aceptable. Si llegas a límites de capacidad de BD, reduce la frecuencia (p. ej., `"*/5"`) o muda a un message broker dedicado (Redis, Cloud Tasks via HTTP).

---

## 4. Escribir tareas

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
        subject="¡Bienvenido a MyCoolProject!",
        message=f"Hola {user.first_name}, ¡bienvenido a bordo!",
        from_email="noreply@mycoolproject.cl",
        recipient_list=[user.email],
        fail_silently=False,
    )
```

Llámala desde cualquier parte de tu código:

```python
# En una vista, servicio o señal
from .tasks import send_welcome_email

send_welcome_email.enqueue(user.id)
# .enqueue() guarda la tarea en la BD y retorna inmediatamente.
# El db_worker poll las tareas pendientes y las ejecuta en segundo plano.
```

### Tareas programadas (retrasadas)

```python
from django.tasks import schedule
from datetime import timedelta

# Ejecutar 1 hora desde ahora
schedule("mycoolproject.tasks.send_welcome_email", args=[user.id], delay=timedelta(hours=1))
```

---

## 5. Elige tu opción de worker

Ambas opciones están listas para producción. Elige según tu presupuesto y necesidades de escala:

| | Opción A: Cloud Tasks HTTP | Opción B: Worker embebido |
|---|---|---|
| Costo extra | ~$0 (dentro del nivel gratuito) | ~$10–20/mes (instancia siempre activa) |
| Escalar a cero | Sí | No |
| Latencia de tareas | Segundos | Segundos |
| Carga de BD | Ninguna | Una conexión 24/7 |
| Complejidad de configuración | Media | Baja |
| Listo para producción | Sí (con IAM bloqueado) | Sí |

**Recomendación:** Empieza con la **Opción A (Cloud Tasks)** — no tiene costo extra, escala a cero significa que no pagas nada cuando no hay tráfico, y Cloud Tasks maneja reintentos con backoff automáticamente. La Opción B es una alternativa válida si prefieres mantener todo en un contenedor sin ninguna dependencia de servicio externo.

---

## 6. Limitaciones

- **`DatabaseBackend`** (Opción B) mantiene una conexión de BD ocupada 24/7. Monitorea el uso de conexiones de `db-f1-micro`.
- Las tareas en la tabla de BD son recogidas por **un worker por instancia**. Con múltiples instancias de Cloud Run, cada una poll independientemente — las tareas pueden ejecutarse más de una vez si no son idempotentes. Usa `--max-instances=1` en Cloud Run si la ejecución exacta importa.
- Cloud Tasks **Opción A** límite de payload: **100 KB** por tarea. Pasa IDs, obtiene objetos dentro del handler.
- El handler en la Opción A debe ser **idempotente** — Cloud Tasks puede entregar al menos una vez.
- No existe aún un paquete oficial de backend Cloud Tasks para `django.tasks` como paquete estable. La integración HTTP en la Opción A es un workaround manual hasta que haya un backend de tercero disponible. Revisa [djangoproject.com/en/6.0/topics/tasks](https://docs.djangoproject.com/en/6.0/topics/tasks) para la lista actual de backends de terceros.

---

## 7. Implementación

Elige tu opción de worker:

- **[13.A — Cloud Tasks via HTTP (Recomendado)](13_django_tasks_cloud_tasks.es.md)** — escala a cero, sin poll de BD, ~$0/mes
- **[13.B — db_worker embebido (Alternativa)](13_django_tasks_embedded.es.md)** — configuración más simple, requiere instancia siempre activa

---

## 📖 Navegación

- [01 — Configuración del Proyecto GCP](01_gcp_setup.es.md)
- [02 — Artifact Registry](02_artifact_registry.es.md)
- [03 — Cloud SQL (Base de datos PostgreSQL)](03_cloud_sql.es.md)
- [04 — Secret Manager](04_secret_manager.es.md)
- [05 — Cloud Storage (Archivos media y static)](05_cloud_storage.es.md)
- [06 — Dockerfile](06_dockerfile.es.md)
- [07 — Primer Despliegue](07_first_deploy.es.md)
- [08 — Dominio Personalizado y SSL](08_domain_ssl.es.md)
- [09 — Workload Identity Federation (Autenticación sin claves en GitHub Actions)](09_workload_identity.es.md)
- [10 — Pipeline CI/CD con GitHub Actions](10_github_actions.es.md)
- [11 — Referencia Rápida](11_quick_reference.es.md)
- [12 — Bonus: Email Personalizado (@dominio.cl)](12_custom_email.es.md)
- [13 — Bonus: Django Tasks](13_django_tasks.es.md) *(capítulo actual)*
  - [13.A — Cloud Tasks via HTTP](13_django_tasks_cloud_tasks.es.md)
  - [13.B — db_worker embebido](13_django_tasks_embedded.es.md)