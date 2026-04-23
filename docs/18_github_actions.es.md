---
description: "Configura un pipeline CI/CD completamente automatizado usando GitHub Actions que prueba, construye y despliega tu app Django en cada push."
image: assets/social-banner.png
---

# 17 — GitHub Actions CI/CD

← [Anterior: 16 — Workload Identity Federation](17_wif.es.md)

Este capítulo crea el workflow de GitHub Actions que automatiza todo el proceso de despliegue. Cada push a `main` ejecutará automáticamente: pruebas, construcción de la imagen Docker, empuje a Artifact Registry, migraciones, y despliegue a Cloud Run.

---

## Qué queremos que ocurra

En **cada push a `main`**:
1. Ejecutar pruebas
2. Construir imagen Docker
3. Empujar a Artifact Registry (dos etiquetas: `latest` + `<git-sha>`)
4. Ejecutar migraciones de base de datos en PlanetScale
5. Desplegar a Cloud Run

En **cada pull request**:
1. Solo ejecutar pruebas (sin despliegue)

---

## Crear el archivo de workflow

Crea `.github/workflows/deploy.yml` en la raíz del repo:

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
  # ── Job 1: test ─────────────────────────────────────────────────────────────
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

  # ── Job 2: deploy ────────────────────────────────────────────────────────────
  deploy:
    runs-on: ubuntu-latest
    needs: test
    if: github.ref == 'refs/heads/main'

    permissions:
      contents: read
      id-token: write

    steps:
      - uses: actions/checkout@v4

      # Autenticarse en GCP usando Workload Identity
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}

      # Instalar CLI de gcloud
      - uses: google-github-actions/setup-gcloud@v2

      # Configurar Docker para empujar a Artifact Registry
      - name: Configure Docker
        run: gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev --quiet

      # Construir imagen con dos etiquetas
      - name: Build image
        run: |
          docker build \
            -t ${{ env.IMAGE }}:${{ github.sha }} \
            -t ${{ env.IMAGE }}:latest \
            .

      # Empujar ambas etiquetas
      - name: Push image
        run: docker push --all-tags ${{ env.IMAGE }}

      # Actualizar el servicio Cloud Run para usar la nueva imagen
      - name: Deploy to Cloud Run
        run: |
          gcloud run services update mycoolproject \
            --image=${{ env.IMAGE }}:${{ github.sha }} \
            --region=${{ env.REGION }}

      # Ejecutar migraciones via Cloud Run Job
      - name: Run migrations
        run: |
          gcloud run jobs execute migrate \
            --region=${{ env.REGION }} \
            --wait
```

---

## Cómo funciona paso a paso

### En push a main

```
push a main
    │
    ├── test job
    │     ├── checkout del código
    │     ├── instalar uv + dependencias
    │     └── ejecutar pruebas
    │               │
    │          ¿falla? → workflow se detiene, no hay deploy
    │          ¿pasa? ↓
    │
    └── deploy job
          ├── autenticarse en GCP (Workload Identity)
          ├── docker build (usa layer cache)
          ├── docker push → Artifact Registry
          └── gcloud run services update → nueva revisión en vivo
```

### En pull request

```
PR push
    │
    └── test job
          ├── checkout
          ├── instalar deps
          └── ejecutar pruebas
                   │
              ¿falla? → PR bloqueado
              ¿pasa? → PR listo para merging
```

El job de deploy se omite porque `github.ref` no es `refs/heads/main`.

---

## Permisos del workflow

El bloque `permissions` es importante:

```yaml
permissions:
  contents: read      # Leer el repo
  id-token: write     # Permitir intercambio de token OIDC (para Workload Identity)
```

`id-token: write` es requerido para que Workload Identity funcione — permite al workflow intercambiar un token OIDC por un access token de GCP.

---

## Variables de entorno

```yaml
env:
  REGION: southamerica-east1
  IMAGE: southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app
```

Estas son variables a nivel de workflow disponibles para todos los jobs. Si cambias proyecto/región, actualiza aquí.

---

## Las etiquetas de imagen

Empujamos dos etiquetas:

| Etiqueta | Significado | Usado para |
|---|---|---|
| `latest` | Build más reciente | Rollbacks, despliegues de emergencia |
| `<git-sha>` | Única por commit | Rollback preciso a commit específico |

Cloud Run se despliega con `<git-sha>` para poder hacer rollback a este commit exacto si es necesario.

---

## Rollback

Si un mal despliegue se publica, haz rollback en segundos:

```bash
# Listar imágenes recientes en Artifact Registry
gcloud artifacts docker images list southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app

# Actualizar Cloud Run para usar la imagen de un commit anterior
gcloud run services update mycoolproject \
  --image=southamerica-east1-docker.pkg.dev/mycoolproject-prod/app-repo/app:<sha-anterior> \
  --region=southamerica-east1
```

O vía GitHub Actions — vuelve a ejecutar el workflow del commit anterior.

---

## Migraciones en el workflow

Las migraciones se ejecutan como un Cloud Run Job (`migrate`) que creamos en el capítulo 15. El workflow déclenche este job con `--wait` para que complete antes de que el tráfico se mueva a la nueva versión.

Para PlanetScale, las migraciones necesitan ser cambios de esquema (create table, add column, etc.) — el comando `migrate` lo maneja.

---

## Secretos en GitHub

Asegúrate de que estos secretos estén establecidos en **GitHub → Settings → Secrets and variables → Actions**:

| Secreto | Valor |
|---|---|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Del capítulo 17 |
| `GCP_SERVICE_ACCOUNT` | `mycoolproject-run@mycoolproject-prod.iam.gserviceaccount.com` |

---

## Verificar el workflow

1. Haz push de un commit a main
2. Ve a la pestaña **GitHub → Actions**
3. Observa el workflow ejecutándose
4. Si succeeds, visita tu URL del sitio
5. Si falla, haz clic en el job fallido para ver los logs

---

## Costo

GitHub Actions da 2,000 minutos gratis al mes para repos privados.

Cada ejecución de deploy toma ~5-10 minutos, así que obtienes ~200-400 despliegues gratis al mes.

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
- 17 — GitHub Actions CI/CD (Capítulo actual)
- [18 — Referencia Rápida](19_quick_reference.es.md)
