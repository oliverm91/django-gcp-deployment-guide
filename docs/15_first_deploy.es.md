---
description: "Despliega manualmente tu app Django a Cloud Run por primera vez para verificar que toda la infraestructura funciona."
image: assets/social-banner.png
---

# 14 — Primer Despliegue

← [Anterior: 13 — Dockerfile](14_dockerfile.es.md)

Este capítulo guía a través del despliegue a Cloud Run manualmente por primera vez. Después de esto, GitHub Actions lo manejará automáticamente.

---

## Requisitos previos

Antes de desplegar, asegúrate de tener:

1. **Todos los recursos de Terraform creados** (capítulos 05-13)
2. **Secretos establecidos en Secret Manager** (capítulo 08)
3. **Imagen Docker construida y empujada** a Artifact Registry
4. **Base de datos PlanetScale creada** (capítulo 04)
5. **Dominio apuntando a Cloud Run** (o omite esto por ahora — usa la URL `.run.app`)

---

## Paso 1: Autenticar Docker en Artifact Registry

```bash
gcloud auth configure-docker southamerica-east1-docker.pkg.dev
```

---

## Paso 2: Construir y empujar la imagen Docker

```bash
# Establecer la URL de la imagen
IMAGE="southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app"

# Construir con dos etiquetas
docker build -t $IMAGE:latest -t $IMAGE:$(git rev-parse --short HEAD) .

# Empujar ambas etiquetas
docker push --all-tags $IMAGE
```

---

## Paso 3: Establecer valores de secretos (si aún no se hizo)

```bash
# Database URL (from PlanetScale dashboard)
echo -n "postgres://user:password@aws.connect.psdb.cloud/mycoolproject?sslmode=require" \
  | gcloud secrets versions add DATABASE_URL --data-file=-

# Django secret key
python -c "import secrets; print(secrets.token_urlsafe(50))"
echo -n "<generated-key>" | gcloud secrets versions add DJANGO_SECRET_KEY --data-file=-

# ALLOWED_HOSTS
echo -n "mycoolproject.com,www.mycoolproject.com" | gcloud secrets versions add ALLOWED_HOSTS --data-file=-
```

---

## Paso 4: Verificar que Cloud Run está desplegado

```bash
# Obtener la URL del servicio
gcloud run services describe mycoolproject --region=southamerica-east1 --format="value(status.url)"

# Probar el endpoint de health
curl https://<url>/health/
```

Debería retornar `{"status": "ok"}`.

---

## Paso 5: Ejecutar migraciones en PlanetScale

Como no podemos usar `gcloud sql` (no hay Cloud SQL), usamos un Cloud Run Job para ejecutar migraciones:

```bash
# Crear un job temporal para ejecutar migraciones
gcloud run jobs create migrate \
  --image=$IMAGE:latest \
  --region=southamerica-east1 \
  --service-account=mycoolproject-worker@mycoolproject-prod.iam.gserviceaccount.com \
  --set-env-vars=DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest \
  --command="uv,run,manage.py,migrate"

# Ejecutarlo
gcloud run jobs execute migrate --region=southamerica-east1 --wait
```

---

## Paso 6: Collectstatic

Subir archivos estáticos a Cloud Storage:

```bash
docker run --rm \
  -e DATABASE_URL=DATABASE_URL:latest \
  -e SECRET_KEY=DJANGO_SECRET_KEY:latest \
  -e DJANGO_SETTINGS_MODULE=core.settings.prod \
  -e GS_PROJECT_ID=mycoolproject-prod \
  $IMAGE:latest \
  uv run manage.py collectstatic --noinput
```

Esto no funcionará — necesita acceso a Secret Manager. En su lugar, usa un Cloud Run Job:

```bash
# Crear job para collectstatic
gcloud run jobs create collectstatic \
  --image=$IMAGE:latest \
  --region=southamerica-east1 \
  --service-account=mycoolproject-worker@mycoolproject-prod.iam.gserviceaccount.com \
  --set-secrets=DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest,GS_PROJECT_ID=mycoolproject-prod:latest \
  --command="uv,run,manage.py,collectstatic,--noinput"

# Ejecutarlo
gcloud run jobs execute collectstatic --region=southamerica-east1 --wait
```

---

## Verificar que todo funciona

```bash
# Probar el sitio
curl https://mycoolproject-<hash>-uc.a.run.app/

# Ver logs
gcloud run services logs tail mycoolproject --region=southamerica-east1
```

---

## Si algo sale mal

### Revisar los logs

```bash
gcloud run services logs tail mycoolproject --region=southamerica-east1
```

### Revisar las revisiones de Cloud Run

```bash
gcloud run revisions list --service=mycoolproject --region=southamerica-east1
```

### Hacer rollback a una imagen anterior

```bash
# Obtener la etiqueta de la imagen anterior (del historial de git o Artifact Registry)
docker pull southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:<previous-sha>

# Actualizar Cloud Run
gcloud run services update mycoolproject \
  --image=southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:<previous-sha> \
  --region=southamerica-east1
```

---

## Qué sigue

Ahora que la app está desplegada, necesitamos:
- Dominio personalizado + SSL (capítulo 15)
- Workload Identity Federation para GitHub Actions (capítulo 16)
- Pipeline CI/CD de GitHub Actions (capítulo 17)

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
- [12 — Cloud Tasks y Scheduler](13_tasks.es.md)
- [13 — Dockerfile](14_dockerfile.es.md)
- 14 — Primer Despliegue (Capítulo actual)
- [15 — Dominio personalizado y SSL](16_domain_ssl.es.md)
- [16 — Workload Identity Federation](17_wif.es.md)
- [17 — GitHub Actions CI/CD](18_github_actions.es.md)
- [18 — Referencia Rápida](19_quick_reference.es.md)
