---
description: "Una guía de referencia rápida y hoja de trucos con todos los comandos de gcloud y despliegue usados en la guía de Cloud Run para Django."
image: assets/social-banner.png

---
# 11 — Referencia Rápida

← [Anterior: 10 — Pipeline CI/CD con GitHub Actions](10_github_actions.es.md)

## Despliegue manual (mismos pasos que GitHub Actions)

```bash
IMAGE="southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/app"

docker build -t $IMAGE:latest .    # Construir imagen desde el Dockerfile en la raíz del repositorio
docker push $IMAGE:latest          # Subir imagen a Artifact Registry

gcloud run jobs update migrate --image=$IMAGE:latest --region=southamerica-east1  # Apuntar el trabajo de migración a la nueva imagen
gcloud run jobs execute migrate --region=southamerica-east1 --wait                # Ejecutar migraciones, esperar a que terminen

gcloud run deploy mycoolproject --image=$IMAGE:latest --region=southamerica-east1  # Desplegar nueva imagen a Cloud Run
```

## Ejecutar migraciones sin reconstruir

```bash
gcloud run jobs execute migrate --region=southamerica-east1 --wait
```

## Ver logs en vivo

```bash
# Transmitir logs en vivo a la terminal — útil justo después de un despliegue (Ctrl+C para detener)
gcloud run services logs tail mycoolproject --region=southamerica-east1

# Lee las últimas 50 entradas de log de nivel error desde Cloud Logging
gcloud logging read \
  'resource.type="cloud_run_revision" AND severity>=ERROR' \
  --project=mycoolproject-prod --limit=50
```

## Secretos

```bash
# Añadir un nuevo secreto
echo -n "valor" | gcloud secrets create NOMBRE_SECRETO --data-file=-

# Actualizar un secreto existente
echo -n "nuevo-valor" | gcloud secrets versions add NOMBRE_SECRETO --data-file=-

# Leer un secreto (cuidado — se imprime en la terminal)
gcloud secrets versions access latest --secret=NOMBRE_SECRETO

# Listar todos los secretos
gcloud secrets list
```

## Cloud Run

```bash
# Muestra detalles del servicio, URL, revisión actual y división de tráfico
gcloud run services describe mycoolproject --region=southamerica-east1

# Lista revisiones (la más reciente primero) — usar para encontrar el nombre de la revisión para rollback
gcloud run revisions list --service=mycoolproject --region=southamerica-east1

# Cambia instantáneamente el 100% del tráfico a una revisión anterior (rollback instantáneo)
gcloud run services update-traffic mycoolproject \
  --region=southamerica-east1 \
  --to-revisions=mycoolproject-<nombre-revision>=100

# Actualiza una variable de entorno en el servicio en vivo sin reconstruir la imagen
gcloud run services update mycoolproject \
  --region=southamerica-east1 \
  --update-env-vars=ALLOWED_HOSTS="mycoolproject.cl,www.mycoolproject.cl"
```

## Cloud SQL

```bash
# Imprime el estado de la instancia (RUNNABLE = saludable, SUSPENDED = pausada para ahorrar costos)
gcloud sql instances describe mycoolproject-db --format="value(state)"

# Abre una sesión interactiva de psql a la base de datos de producción mediante el proxy de Cloud SQL
# Usar con cuidado — es acceso directo a los datos de producción
gcloud sql connect mycoolproject-db --user=djangouser --database=mycoolproject
```

## Comandos de gestión de Django mediante Cloud Run Job

Para cualquier comando `manage.py` puntual en producción, crea o reutiliza un Cloud Run Job:

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

## Archivos estáticos

```bash
# Volver a subir archivos estáticos a GCS después de cambios en CSS/JS/iconos
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
