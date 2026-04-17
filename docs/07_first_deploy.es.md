---
description: "Despliega manualmente tu app Django en Cloud Run por primera vez para verificar el funcionamiento de extremo a extremo."
image: assets/social-banner.png

---
# 07 — Primer Despliegue

← [Anterior: 06 — Dockerfile](06_dockerfile.md)

> ✅ **Cloud Run es gratuito con tráfico bajo.** Nivel gratuito: 2 millones de solicitudes/mes, 360.000 GB-segundos de CPU, 180.000 GB-segundos de memoria. Con `--min-instances=0`, el servicio escala a cero cuando está inactivo — sin solicitudes, sin costo. Un marketplace pequeño típico se mantiene dentro del nivel gratuito durante meses.

Este capítulo despliega MyCoolProject en Cloud Run por primera vez. Esto se hace manualmente desde tu máquina local. Después de esto, GitHub Actions se encarga de todos los despliegues posteriores.

---

## Arquitectura en tiempo de ejecución

Antes de ejecutar el despliegue, veamos exactamente qué estamos construyendo. El contenedor de producción final actúa como el cerebro de la operación, comunicándose dinámicamente con nuestra suite de servicios GCP configurados:

![Diagrama de componentes de arquitectura en tiempo de ejecución](assets/diagram-runtime.svg)

---

## Construir y subir la imagen

> El proyecto `mycoolproject-prod` y el registro `mycoolproject-repo` deben existir (creados en los [capítulos 01](01_gcp_setup.md) y [02](02_artifact_registry.md)). Este comando crea la imagen `app` dentro de ese registro.

Ejecuta desde la raíz del repositorio local:

```bash
IMAGE="southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/app"

# Configura Docker para usar credenciales de gcloud para este registro. Una vez por máquina.
# Después de esto, docker push/pull a este registro funciona sin un paso de login separado.
gcloud auth configure-docker southamerica-east1-docker.pkg.dev

# Construye la imagen Docker desde el Dockerfile en la raíz del repositorio y la etiqueta con la
# ruta completa de Artifact Registry para que docker push sepa a dónde enviarla.
docker build -t $IMAGE:latest .

# Sube la imagen a Artifact Registry. Cloud Run la descargará desde aquí al desplegar.
# Resultado: visible en console.cloud.google.com/artifacts/docker/mycoolproject-prod
docker push $IMAGE:latest
```

---

## Desplegar en Cloud Run

### ¿Qué es Cloud Run?

Cloud Run es una plataforma de contenedores serverless. Le das una imagen Docker y ella:

- Inicia instancias del contenedor para manejar solicitudes entrantes
- Escala a cero cuando no hay tráfico (sin costo cuando está inactivo)
- Escala automáticamente bajo carga
- Proporciona una URL HTTPS pública automáticamente
- Gestiona certificados SSL automáticamente

Nunca aprovisionas servidores, instalas parches del SO ni configuras balanceadores de carga.

```bash
# Despliega la imagen en Cloud Run por primera vez, creando un nuevo servicio llamado "mycoolproject".
# Los despliegues posteriores solo necesitan: gcloud run deploy mycoolproject --image=... --region=...
# (Todos los demás flags son recordados por el servicio después del primer despliegue.)
# Resultado: imprime la URL del servicio cuando completa — visítala para confirmar que el sitio está activo.
# También visible en console.cloud.google.com/run/detail/southamerica-east1/mycoolproject
gcloud run deploy mycoolproject \
  --image=$IMAGE:latest \
  --region=southamerica-east1 \
  --platform=managed \
  --allow-unauthenticated \
  --service-account=mycoolproject-run-sa@mycoolproject-prod.iam.gserviceaccount.com \
  --add-cloudsql-instances=mycoolproject-prod:southamerica-east1:mycoolproject-db \
  --set-secrets=DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest,GOOGLE_CLIENT_ID=GOOGLE_CLIENT_ID:latest,GOOGLE_CLIENT_SECRET=GOOGLE_CLIENT_SECRET:latest,EMAIL_HOST=EMAIL_HOST:latest,EMAIL_PORT=EMAIL_PORT:latest,EMAIL_HOST_USER=EMAIL_HOST_USER:latest,EMAIL_HOST_PASSWORD=EMAIL_HOST_PASSWORD:latest,DIDIT_API_KEY=DIDIT_API_KEY:latest,DIDIT_WORKFLOW_ID=DIDIT_WORKFLOW_ID:latest,DIDIT_WEBHOOK_SECRET=DIDIT_WEBHOOK_SECRET:latest \
  --set-env-vars=ALLOWED_HOSTS=mycoolproject.cl \
  --min-instances=0 \
  --max-instances=5 \
  --memory=512Mi \
  --cpu=1
```

Flags explicados:

| Flag | Significado |
|---|---|
| `--allow-unauthenticated` | Internet puede acceder al servicio (requerido para un sitio web público) |
| `--service-account` | El contenedor se ejecuta como `mycoolproject-run-sa` — obtiene sus permisos de GCS/SQL/Secret automáticamente |
| `--add-cloudsql-instances` | Adjunta el proxy de Cloud SQL — habilita la conexión por socket Unix a la base de datos |
| `--set-secrets` | Obtiene estos secrets de Secret Manager y los inyecta como variables de entorno |
| `--set-env-vars` | Variables de entorno planas (no secretas) |
| `--min-instances=0` | **Escalar a cero cuando está inactivo.** Sin costo cuando el tráfico se detiene. Arranque en frío: la primera solicitud después de inactividad tarda ~1–2 s (arranque del contenedor + conexión a BD). Bueno para sitios con bajo tráfico. **vs** `--min-instances=1` mantiene una instancia siempre activa: respuesta inmediata, pero cuesta ~$5–10/mes siempre (incluso sin tráfico). Elige 0 para desarrollo/bajo tráfico; elige 1 si la respuesta por debajo de un segundo es crítica. |
| `--max-instances=5` | Límite máximo de instancias de contenedor concurrentes |
| `--memory=512Mi` | RAM por instancia de contenedor |

Después del despliegue, gcloud imprime la URL del servicio: `https://mycoolproject-<hash>-uc.a.run.app`

---

## Ejecutar migraciones de base de datos

### ¿Qué es un Cloud Run Job?

Un Cloud Run Job es una ejecución de contenedor única — se ejecuta hasta completarse y sale, a diferencia de un Cloud Run Service que permanece activo para manejar tráfico HTTP. Los Jobs son ideales para `manage.py migrate` — quieres ejecutar migraciones exactamente una vez por despliegue, no en cada solicitud.

Crea el job de migración (una vez):

```bash
# Crea un Cloud Run Job llamado "migrate". Un Job es una ejecución de contenedor única
# (se ejecuta hasta completarse y sale), a diferencia de un Service que maneja tráfico HTTP continuo.
# Este job ejecuta `manage.py migrate` contra la base de datos de producción.
# Solo necesita crearse una vez — GitHub Actions actualiza su imagen en cada despliegue.
# Resultado: visible en console.cloud.google.com/run/jobs
gcloud run jobs create migrate \
  --image=$IMAGE:latest \
  --region=southamerica-east1 \
  --service-account=mycoolproject-run-sa@mycoolproject-prod.iam.gserviceaccount.com \
  --add-cloudsql-instances=mycoolproject-prod:southamerica-east1:mycoolproject-db \
  --set-secrets=DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest \
  --command="uv,run,manage.py,migrate"
```

Ejecútalo y espera a que termine:

```bash
# Ejecuta el job de migración y espera a que termine antes de retornar.
# --wait bloquea tu terminal y transmite la salida — verás el log de migración de Django.
# Si las migraciones fallan, el comando sale con código diferente de cero e imprime el error.
# Resultado: log de ejecución visible en console.cloud.google.com/run/jobs/details/southamerica-east1/migrate
gcloud run jobs execute migrate --region=southamerica-east1 --wait
```

`--wait` bloquea tu terminal hasta que el job se completa e imprime la salida. Si las migraciones fallan, el job sale con un código diferente de cero y verás el error.

En despliegues posteriores, GitHub Actions actualiza la imagen del job y lo vuelve a ejecutar automáticamente antes de desplegar la nueva revisión del servicio.

---

## Verificar el despliegue

```bash
# Imprime la URL pública del servicio desplegado.
# Pégala en tu navegador para confirmar que el sitio es accesible.
gcloud run services describe mycoolproject \

  --region=southamerica-east1 \
  --format="value(status.url)"

# Transmite logs en vivo de los contenedores en ejecución a tu terminal (Ctrl+C para detener).
# Útil para observar las solicitudes entrantes y detectar errores justo después del despliegue.
# Los logs también se almacenan permanentemente en console.cloud.google.com/logs
gcloud run services logs tail mycoolproject --region=southamerica-east1
```

Visita `<url>/health/` — debería retornar `{"status": "ok"}`.

---

## Superusuario de Django (una vez)

No puedes ejecutar `manage.py createsuperuser` de forma interactiva en Cloud Run. En cambio, usa el enfoque de Cloud Run Jobs:

```bash
# Crea un job único para ejecutar createsuperuser de forma no interactiva.
# --noinput lee el email/contraseña desde variables de entorno en lugar de pedirlos.
# Usa una contraseña temporal aquí — cámbiala inmediatamente después del primer login en /admin/.
gcloud run jobs create createsuperuser \

  --image=$IMAGE:latest \
  --region=southamerica-east1 \
  --service-account=mycoolproject-run-sa@mycoolproject-prod.iam.gserviceaccount.com \
  --add-cloudsql-instances=mycoolproject-prod:southamerica-east1:mycoolproject-db \
  --set-secrets=DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest \
  --set-env-vars=DJANGO_SUPERUSER_EMAIL=admin@mycoolproject.cl,DJANGO_SUPERUSER_PASSWORD=<contraseña-temporal> \
  --command="uv,run,manage.py,createsuperuser,--noinput"

# Ejecuta el job y espera. Al completarse, inicia sesión en <url-del-servicio>/admin/ con la contraseña temporal.
gcloud run jobs execute createsuperuser --region=southamerica-east1 --wait
```

Cambia la contraseña inmediatamente después del primer inicio de sesión.

---

## 📖 Navegación

- [01 — Configuración del Proyecto GCP](01_gcp_setup.es.md)
- [02 — Artifact Registry](02_artifact_registry.es.md)
- [03 — Cloud SQL (Base de datos PostgreSQL)](03_cloud_sql.es.md)
- [04 — Secret Manager](04_secret_manager.es.md)
- [05 — Cloud Storage (Media & static files)](05_cloud_storage.es.md)
- [06 — Dockerfile](06_dockerfile.es.md)
- 07 — Primer Despliegue (Capítulo actual)
- [08 — Dominio Personalizado y SSL](08_domain_ssl.es.md)
- [09 — Workload Identity Federation (Auth de GitHub sin llaves)](09_workload_identity.es.md)
- [10 — Pipeline CI/CD con GitHub Actions](10_github_actions.es.md)
- [11 — Referencia Rápida](11_quick_reference.es.md)
- [12 — Bonus: Email Personalizado (@dominio.cl)](12_custom_email.es.md)
- [13 — Bonus: Django Tasks](13_django_tasks.es.md)
