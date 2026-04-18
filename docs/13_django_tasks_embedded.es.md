---
description: "Ejecuta db_worker dentro de tu contenedor de Cloud Run — configuración más simple, requiere instancia siempre activa."
image: assets/social-banner.png
---
# 13.B — db_worker embebido (Alternativa)

← [Anterior: 13 — Bonus: Django Tasks](13_django_tasks.es.md) | [Siguiente: 13.A — Cloud Tasks via HTTP](13_django_tasks_cloud_tasks.es.md) →

Si prefieres mantener todo en un proceso sin ninguna dependencia de servicio externo, ejecuta el `db_worker` dentro de tu contenedor de Cloud Run. Cloud Run despierta el handler web cuando llega una solicitud, y el worker en segundo plano del mismo contenedor poll la base de datos buscando tareas.

> **Nota de costo:** esta opción requiere `--min-instances=1` + `--no-cpu-throttling` para mantener el worker ejecutándose. Esto cuesta aproximadamente **$10–20/mes** — no es gratis. Usa la [Opción A (Cloud Tasks)](13_django_tasks_cloud_tasks.es.md) si necesitas escala a cero.

---

## Paso 1: Actualizar el script de inicio

Crea `start.sh` en la raíz del proyecto:

```bash
#!/bin/bash
# start.sh — ejecuta gunicorn (web) y db_worker (runner de tareas) juntos.
# Usar trap asegura que ambos procesos reciban SIGTERM al apagar el contenedor.

# Iniciar db_worker en segundo plano
python manage.py db_worker &
DB_WORKER_PID=$!

# Capturar SIGTERM y reenviarlo a ambos procesos
trap "kill -TERM $DB_WORKER_PID; wait $DB_WORKER_PID" SIGTERM

# Iniciar gunicorn como PID 1 (exec asegura que sea PID 1 — el SIGTERM de Cloud Run le llega limpiamente)
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

---

## Paso 2: Actualizar el Dockerfile

```dockerfile
# ... contenido existente del Dockerfile ...

# Usar script de inicio personalizado
CMD ["./start.sh"]
```

---

## Paso 3: Actualizar el servicio de Cloud Run

El worker necesita CPU asignada continuamente (no limitada entre solicitudes):

```bash
gcloud run services update mycoolproject \
  --region=southamerica-east1 \
  --no-cpu-throttling \
  --min-instances=1
```

> **Explicación del throttle de CPU:** por defecto, Cloud Run solo asigna CPU durante el procesamiento de solicitudes. Cuando está inactivo, el CPU se limita a cero. El `db_worker` poll la base de datos cada segundo — si el CPU se limita entre solicitudes, el polling se detiene y las tareas se acumulan. `--no-cpu-throttling` mantiene el CPU ejecutándose incluso cuando no hay tráfico, para que el worker pueda seguir poll-eando. Por esto se requiere `--min-instances=1` — la instancia debe permanecer caliente para mantener el worker vivo.

---

## Polling de tareas e instancias múltiples

Con `DatabaseBackend`, cada instancia de Cloud Run ejecuta su propio `db_worker` que poll la base de datos independientemente. Si ejecutas múltiples instancias (`--max-instances > 1`), cada worker poll simultáneamente y la misma tarea puede ser recogida por más de una instancia.

**Si la ejecución exacta importa** (ej. enviar dos emails para un registro): establece `--max-instances=1` para que solo una instancia ever run, garantizando que el worker recoge cada tarea exactamente una vez.

**Si puedes tolerar al-menos-una-vez** (ej. procesamiento de imágenes que verifica "ya procesado" antes de ejecutar): escala libremente — Cloud Tasks maneja esto con visibility timeout; el worker embebido lo maneja marcando la tarea como completada antes de que otra instancia pueda recogerla.

---

## 📖 Navegación

- [13 — Bonus: Django Tasks](13_django_tasks.es.md)
- [13.A — Cloud Tasks via HTTP](13_django_tasks_cloud_tasks.es.md)
- [13.B — db_worker embebido (Actual)](13_django_tasks_embedded.es.md)