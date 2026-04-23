---
description: "Una guía de referencia rápida para todos los comandos de Terraform, gcloud y otros snippets útiles usados en esta guía."
image: assets/social-banner.png
---

# 18 — Referencia Rápida

← [Anterior: 17 — GitHub Actions CI/CD](18_github_actions.es.md)

Todos los comandos importantes de esta guía en un solo lugar.

---

## Terraform

```bash
cd infrastructure

terraform init               # Inicializar (descargar providers, setup backend)
terraform plan               # Previsualizar cambios (sin cambios reales)
terraform apply              # Aplicar cambios (crea/actualiza recursos)
terraform apply -auto-approve # Aplicar sin confirmación
terraform destroy            # Eliminar todos los recursos manejados por Terraform
terraform show               # Mostrar estado actual
terraform output             # Mostrar valores de output
terraform state list         # Listar todos los recursos en el estado
terraform refresh            # Sincronizar estado con infraestructura real
```

---

## Variables de Terraform

```bash
# Establecer variable via CLI
terraform plan -var="project_id=my-project"

# O en terraform.tfvars (no comprometido a git)
echo 'project_id = "my-project"' > terraform.tfvars
```

---

## Proyecto GCP y APIs

```bash
# Obtener proyecto actual
gcloud config get-value project

# Establecer proyecto
gcloud config set project mycoolproject-prod

# Obtener número de proyecto
gcloud projects describe mycoolproject-prod --format='value(projectNumber)'

# Listar APIs habilitadas
gcloud services list --enabled --project=mycoolproject-prod
```

---

## Artifact Registry

```bash
# Autenticar Docker
gcloud auth configure-docker southamerica-east1-docker.pkg.dev

# Listar repositorios
gcloud artifacts repositories list --project=mycoolproject-prod

# Listar imágenes en un repositorio
gcloud artifacts docker images list southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo
```

---

## Cloud Run

```bash
# Desplegar una nueva imagen
gcloud run deploy mycoolproject \
  --image=southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:latest \
  --region=southamerica-east1

# Obtener URL del servicio
gcloud run services describe mycoolproject --region=southamerica-east1 --format="value(status.url)"

# Ver logs
gcloud run services logs tail mycoolproject --region=southamerica-east1

# Listar revisiones
gcloud run revisions list --service=mycoolproject --region=southamerica-east1

# Rollback a revisión anterior
gcloud run services update-traffic mycoolproject \
  --region=southamerica-east1 \
  --to-revisions=mycoolproject-<revisión>=100

# Actualizar env vars
gcloud run services update mycoolproject \
  --region=southamerica-east1 \
  --update-env-vars=ALLOWED_HOSTS="mycoolproject.com,www.mycoolproject.com"
```

---

## Cloud Run Jobs

```bash
# Crear un job
gcloud run jobs create job-name \
  --image=southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:latest \
  --region=southamerica-east1

# Ejecutar un job (y esperar)
gcloud run jobs execute job-name --region=southamerica-east1 --wait

# Listar jobs
gcloud run jobs list --region=southamerica-east1
```

---

## Cloud Tasks

```bash
# Listar colas
gcloud tasks queues list --location=southamerica-east1

# Purge una cola (eliminar todos los tasks)
gcloud tasks queues purge mycoolproject-default --location=southamerica-east1
```

---

## Cloud Scheduler

```bash
# Crear un scheduler job (dispara Cloud Run Job)
gcloud scheduler jobs create http worker-trigger \
  --schedule="* * * * *" \
  --uri="https://region-run.googleapis.com/v2/projects/mycoolproject-prod/locations/southamerica-east1/jobs/mycoolproject-worker:run" \
  --http-method=POST \
  --oidc-service-account-email=mycoolproject-scheduler@mycoolproject-prod.iam.gserviceaccount.com

# Listar jobs
gcloud scheduler jobs list --location=southamerica-east1

# Pausar un job
gcloud scheduler jobs pause worker-trigger --location=southamerica-east1

# Reanudar un job
gcloud scheduler jobs resume worker-trigger --location=southamerica-east1
```

---

## Cloud Storage

```bash
# Listar buckets
gsutil ls

# Listar contenido de bucket
gsutil ls gs://mycoolproject-prod-static/

# Hacer bucket público
gsutil iam ch allUsers:objectViewer gs://mycoolproject-prod-static

# Subir archivo
gsutil cp file.txt gs://mycoolproject-prod-media/

# Descargar archivo
gsutil cp gs://mycoolproject-prod-media/file.txt ./

# Establecer cache control en archivos
gsutil setmeta -h "Cache-Control:public, max-age=31536000" gs://mycoolproject-prod-static/**/*.css
```

---

## Secret Manager

```bash
# Listar secretos
gcloud secrets list

# Crear un secreto
echo -n "valor" | gcloud secrets create SECRET_NAME --data-file=-

# Agregar nueva versión
echo -n "nuevo-valor" | gcloud secrets versions add SECRET_NAME --data-file=-

# Leer un secreto
gcloud secrets versions access latest --secret=SECRET_NAME

# Eliminar un secreto (y todas las versiones)
gcloud secrets delete SECRET_NAME
```

---

## Service Accounts

```bash
# Listar service accounts
gcloud iam service-accounts list --project=mycoolproject-prod

# Otorgar rol IAM
gcloud projects add-iam-policy-binding mycoolproject-prod \
  --member="serviceAccount:name@project.iam.gserviceaccount.com" \
  --role="roles/role-name"

# Remover rol IAM
gcloud projects remove-iam-policy-binding mycoolproject-prod \
  --member="serviceAccount:name@project.iam.gserviceaccount.com" \
  --role="roles/role-name"
```

---

## Workload Identity

```bash
# Obtener nombre del recurso del provider
gcloud iam workload-identity-pools providers describe github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --format="value(name)"
```

---

## Docker

```bash
# Construir imagen
docker build -t mycoolproject-app .

# Ejecutar localmente
docker run --rm -p 8080:8080 \
  -e DATABASE_URL="postgres://..." \
  -e SECRET_KEY="test" \
  mycoolproject-app

# Etiquetar para Artifact Registry
docker tag mycoolproject-app southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:latest

# Empujar
docker push southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:latest
```

---

## PlanetScale CLI

```bash
# Autenticarse
pscale auth login

# Crear base de datos
pscale database create mycoolproject

# Listar bases de datos
pscale database list

# Crear branch
pscale branch create mycoolproject feature-branch

# Listar branches
pscale branch list mycoolproject

# Conectarse a branch (desarrollo local)
pscale connect mycoolproject development

# Eliminar branch
pscale branch delete mycoolproject feature-branch

# Obtener connection string
pscale connection-string mycoolproject main --fetch
```

---

## Comandos de gestión de Django

```bash
cd web

# Ejecutar migraciones (en producción vía Cloud Run Job)
DJANGO_SETTINGS_MODULE=core.settings.prod uv run manage.py migrate

# Collectstatic (subir archivos estáticos a GCS)
DJANGO_SETTINGS_MODULE=core.settings.prod uv run manage.py collectstatic --noinput

# Crear superuser
DJANGO_SETTINGS_MODULE=core.settings.prod uv run manage.py createsuperuser --noinput

# Ejecutar tests
DJANGO_SETTINGS_MODULE=core.settings.test uv run manage.py test
```

---

## Workflow de GitHub Actions

El workflow completo está en `.github/workflows/deploy.yml`:

```yaml
name: Test & Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGION: southamerica-east1
  IMAGE: southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          working-directory: web
      - name: Install dependencies
        run: cd web && uv sync --frozen
      - name: Run tests
        run: cd web && uv run manage.py test web/tests --settings=core.settings.test
        env:
          SECRET_KEY: ci-secret-not-real

  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'
    permissions:
      contents: read
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}
      - uses: google-github-actions/setup-gcloud@v2
      - name: Configure Docker
        run: gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev --quiet
      - name: Build image
        run: |
          docker build \
            -t ${{ env.IMAGE }}:${{ github.sha }} \
            -t ${{ env.IMAGE }}:latest \
            .
      - name: Push image
        run: docker push --all-tags ${{ env.IMAGE }}
      - name: Deploy to Cloud Run
        run: |
          gcloud run services update mycoolproject \
            --image=${{ env.IMAGE }}:${{ github.sha }} \
            --region=${{ env.REGION }}
      - name: Run migrations
        run: |
          gcloud run jobs execute migrate \
            --region=${{ env.REGION }} \
            --wait
```

---

## Health check

```bash
curl https://mycoolproject.com/health/
# Esperado: {"status": "ok"}
```

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
- [14 — Primer Despliegue](15_first_deploy.es.md)
- [15 — Dominio personalizado y SSL](16_domain_ssl.es.md)
- [16 — Workload Identity Federation](17_wif.es.md)
- [17 — GitHub Actions CI/CD](18_github_actions.es.md)
- 18 — Referencia Rápida (Capítulo actual)
