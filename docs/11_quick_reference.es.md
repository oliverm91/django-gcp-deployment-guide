---
description: "Una guía de referencia rápida y hoja de trucos con todos los comandos de gcloud y despliegue usados en la guía de Cloud Run para Django."
image: assets/social-banner.png

---
# 11 — Referencia Rápida

## Despliegue manual (mismos pasos que GitHub Actions)

```bash
IMAGE="southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/app"

docker build -t $IMAGE:latest .    # Construir imagen desde el Dockerfile en la raíz del repositorio
docker push $IMAGE:latest          # Subir imagen a Artifact Registry

gcloud run jobs update migrate --image=$IMAGE:latest --region=southamerica-east1  # Apuntar job de migración a la nueva imagen
gcloud run jobs execute migrate --region=southamerica-east1 --wait                # Ejecutar migraciones y esperar a que terminen

gcloud run deploy mycoolproject --image=$IMAGE:latest --region=southamerica-east1  # Desplegar nueva imagen en Cloud Run
```

## Ejecutar migraciones sin recompilar

```bash
gcloud run jobs execute migrate --region=southamerica-east1 --wait
```

## Ver logs en vivo

```bash
# Transmite logs en vivo al terminal — útil justo después de un despliegue (Ctrl+C para detener)
gcloud run services logs tail mycoolproject --region=southamerica-east1

# Obtiene las últimas 50 entradas de log con nivel de error desde Cloud Logging
gcloud logging read \
  'resource.type="cloud_run_revision" AND severity>=ERROR' \
  --project=mycoolproject-prod --limit=50
```

## Secrets

```bash
# Agregar un nuevo secret
echo -n "valor" | gcloud secrets create NOMBRE_SECRET --data-file=-

# Actualizar un secret existente
echo -n "nuevo-valor" | gcloud secrets versions add NOMBRE_SECRET --data-file=-

# Leer un secret (con cuidado — imprime en el terminal)
gcloud secrets versions access latest --secret=NOMBRE_SECRET

# Listar todos los secrets
gcloud secrets list
```

## Cloud Run

```bash
# Muestra los detalles del servicio, URL, revisión actual y distribución de tráfico
gcloud run services describe mycoolproject --region=southamerica-east1

# Lista las revisiones (las más recientes primero) — usar para encontrar el nombre de revisión para rollback
gcloud run revisions list --service=mycoolproject --region=southamerica-east1

# Desvía instantáneamente el 100% del tráfico a una revisión anterior (rollback instantáneo)
gcloud run services update-traffic mycoolproject \
  --region=southamerica-east1 \
  --to-revisions=mycoolproject-<nombre-revisión>=100

# Actualiza una variable de entorno en el servicio activo sin recompilar la imagen
gcloud run services update mycoolproject \
  --region=southamerica-east1 \
  --update-env-vars=ALLOWED_HOSTS="mycoolproject.cl,www.mycoolproject.cl"
```

## Cloud SQL

```bash
# Imprime el estado de la instancia (RUNNABLE = saludable, SUSPENDED = pausada para ahorrar costo)
gcloud sql instances describe mycoolproject-db --format="value(state)"

# Abre una sesión interactiva de psql a la base de datos de producción via el proxy de Cloud SQL
# Usar con cuidado — esto es acceso directo a los datos de producción
gcloud sql connect mycoolproject-db --user=djangouser --database=mycoolproject
```

## Comandos de gestión de Django via Cloud Run Job

Para cualquier comando único de `manage.py` en producción, crea o reutiliza un Cloud Run Job:

```bash
# Ejemplo: ejecutar un comando de gestión personalizado
gcloud run jobs create mi-comando \
  --image=southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/app:latest \
  --region=southamerica-east1 \
  --service-account=mycoolproject-run-sa@mycoolproject-prod.iam.gserviceaccount.com \
  --add-cloudsql-instances=mycoolproject-prod:southamerica-east1:mycoolproject-db \
  --set-secrets=DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest \
  --command="uv,run,manage.py,tu_comando"

gcloud run jobs execute mi-comando --region=southamerica-east1 --wait
```

## Archivos static

```bash
# Volver a subir archivos static a GCS después de cambios en CSS/JS/íconos
cd web
DJANGO_SETTINGS_MODULE=core.settings.prod uv run manage.py collectstatic --noinput
```

## Health check

```bash
curl https://mycoolproject.cl/health/
# Esperado: {"status": "ok"}
```

---

## 📖 Navegación

- [01 — Configuración del Proyecto GCP](01_gcp_setup.es.md)
- [02 — Artifact Registry](02_artifact_registry.es.md)
- [03 — Cloud SQL (Base de datos PostgreSQL)](03_cloud_sql.es.md)
- [04 — Secret Manager](04_secret_manager.es.md)
- [05 — Cloud Storage (Media & static files)](05_cloud_storage.es.md)
- [06 — Dockerfile](06_dockerfile.es.md)
- [07 — Primer Despliegue](07_first_deploy.es.md)
- [08 — Dominio Personalizado y SSL](08_domain_ssl.es.md)
- [09 — Workload Identity Federation (Auth de GitHub sin llaves)](09_workload_identity.es.md)
- [10 — Pipeline CI/CD con GitHub Actions](10_github_actions.es.md)
- 11 — Referencia Rápida (Capítulo actual)
- [12 — Bonus: Email Personalizado (@dominio.cl)](12_custom_email.es.md)
