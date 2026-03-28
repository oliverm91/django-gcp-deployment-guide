---
description: "Construye un pipeline CI/CD completamente automatizado con GitHub Actions para testear, compilar, ejecutar migraciones y desplegar en Cloud Run."
image: assets/social-banner.png

---
# 10 — Pipeline CI/CD con GitHub Actions

← [Anterior: 09 — Workload Identity Federation (Autenticación sin claves en GitHub Actions)](09_workload_identity.md)

> ✅ **Gratuito para la mayoría de usos.** GitHub Actions otorga 2.000 minutos gratuitos/mes para repositorios privados y minutos ilimitados para repositorios públicos. Cada ejecución de despliegue (pruebas + build + push + deploy) tarda aproximadamente 5–10 minutos, dando ~200–400 despliegues gratuitos/mes en un repo privado. Después del nivel gratuito, los minutos adicionales cuestan $0.008/minuto.

## ¿Qué es GitHub Actions?

GitHub Actions es la plataforma de automatización integrada de GitHub. Defines workflows en archivos YAML dentro de `.github/workflows/`. GitHub los ejecuta en sus propios servidores (llamados runners) en respuesta a eventos — un push, un pull request, un horario.

El workflow aquí se ejecuta en cada push a `main` y en cada pull request apuntando a `main`. Tiene dos jobs:

- **test** — se ejecuta en todos los pushes y PRs; bloquea el despliegue si falla
- **deploy** — solo se ejecuta en pushes a `main` (no en PRs); solo se ejecuta si `test` pasa

---

## Crear el archivo del workflow

Crea `.github/workflows/deploy.yml` en la **raíz del repositorio**:

```yaml
name: Test & Deploy

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  REGION: southamerica-east1
  IMAGE: southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/app

jobs:
  # ── Job 1: test ──────────────────────────────────────────────────────────────
  # Se ejecuta en cada push y PR. Bloquea el despliegue si los tests fallan.
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        # Descarga el código de tu repo en el runner

      - uses: astral-sh/setup-uv@v4
        with:
          working-directory: web
        # Instala uv (el gestor de paquetes) en el runner

      - name: Instalar dependencias
        run: cd web && uv sync --frozen
        # Instala todas las dependencias Python desde uv.lock
        # --frozen: falla si el lockfile está desactualizado

      - name: Ejecutar tests
        run: cd web && uv run manage.py test web/tests --settings=core.settings.test
        # Ejecuta la suite de tests de Django usando SQLite en memoria (no se necesita BD)
        env:
          SECRET_KEY: ci-secret-not-real
          # test.py requiere que SECRET_KEY esté configurada; este valor ficticio está bien para tests

  # ── Job 2: deploy ────────────────────────────────────────────────────────────
  # Solo se ejecuta en pushes a main, solo si el job de test pasó.
  deploy:
    runs-on: ubuntu-latest
    needs: test                              # espera a que el job de test tenga éxito
    if: github.ref == 'refs/heads/main'      # omitir en pull requests

    permissions:
      contents: read
      id-token: write                        # requerido para el intercambio de tokens de Workload Identity

    steps:
      - uses: actions/checkout@v4

      # Autenticarse en GCP usando Workload Identity (sin claves JSON)
      - uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}

      # Instalar gcloud CLI en el runner
      - uses: google-github-actions/setup-gcloud@v2

      # Configurar Docker para subir a Artifact Registry
      - name: Configurar Docker
        run: gcloud auth configure-docker ${{ env.REGION }}-docker.pkg.dev --quiet

      # Construir la imagen Docker con dos tags:
      # - :latest (siempre apunta al más reciente)
      # - :<git-sha> (único por commit — permite rollbacks precisos)
      - name: Construir imagen
        run: |
          docker build \
            -t ${{ env.IMAGE }}:${{ github.sha }} \
            -t ${{ env.IMAGE }}:latest \
            .

      # Subir ambos tags a Artifact Registry
      - name: Subir imagen
        run: docker push --all-tags ${{ env.IMAGE }}

      # Actualizar el job de migración para usar la nueva imagen, luego ejecutarlo
      # Esto aplica cualquier nueva migración de base de datos antes de que el tráfico llegue al nuevo código
      - name: Ejecutar migraciones
        run: |
          gcloud run jobs update migrate \
            --image=${{ env.IMAGE }}:${{ github.sha }} \
            --region=${{ env.REGION }}
          gcloud run jobs execute migrate \
            --region=${{ env.REGION }} \
            --wait

      # Desplegar la nueva imagen en Cloud Run
      # Cloud Run crea una nueva revisión y desvía el 100% del tráfico a ella
      - name: Desplegar en Cloud Run
        run: |
          gcloud run deploy mycoolproject \
            --image=${{ env.IMAGE }}:${{ github.sha }} \
            --region=${{ env.REGION }}
```

## Bloque `env` a nivel de workflow

Al comienzo del workflow, antes de la sección `jobs:`, hay un bloque `env:`:

```yaml
env:
  REGION: southamerica-east1
  IMAGE: southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/app
```

Esto define **variables de entorno a nivel de workflow** — constantes disponibles para cada job y cada paso del archivo. Se referencian más adelante como `${{ env.REGION }}` y `${{ env.IMAGE }}`. La ventaja es que si alguna vez cambias la región o el nombre del proyecto, lo actualizas en exactamente un lugar en lugar de buscar en cada comando `gcloud`.

| Variable | Valor | Por qué está aquí |
|---|---|---|
| `REGION` | `southamerica-east1` | La región GCP donde viven Cloud Run, Artifact Registry y Cloud SQL. Se repite en cada comando `gcloud` y `docker`. |
| `IMAGE` | `southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/app` | La ruta completa en Artifact Registry para la imagen Docker. Desglosada: `<región>-docker.pkg.dev/<proyecto>/<repositorio>/<nombre-imagen>`. Se usa al construir, subir y desplegar. |

> **`env:` vs `secrets:`** — `env:` es para configuración no sensible que estás cómodo commiteando en tu repo. `secrets:` (usado para `GCP_WORKLOAD_IDENTITY_PROVIDER` y `GCP_SERVICE_ACCOUNT`) es para valores sensibles almacenados cifrados en GitHub, nunca visibles en logs ni en el historial del repo.

---

## Qué sucede en cada push a main

```
push a main
    │
    ├── job de test
    │     ├── descargar código
    │     ├── instalar uv + dependencias
    │     └── ejecutar suite de tests de Django (171 tests, ~90 segundos)
    │                   │
    │              ¿falla? → el job de deploy se omite, el código roto nunca llega a producción
    │              ¿pasa? ↓
    │
    └── job de deploy
          ├── autenticarse en GCP (Workload Identity)
          ├── docker build (usa caché de capas — rápido si las dependencias no cambiaron)
          ├── docker push → Artifact Registry
          ├── actualizar imagen del job de migración
          ├── ejecutar job de migración → aplica migraciones de BD → espera a que termine
          └── gcloud run deploy → nueva revisión de Cloud Run sale a producción
```

## Qué sucede en un pull request

Solo se ejecuta el job `test`. El job de deploy se omite porque `github.ref` no es `refs/heads/main`. Esto significa que cada PR tiene sus tests ejecutados, pero el sitio activo solo se actualiza cuando el código se fusiona a `main`.

---

## Rollback

Si un mal despliegue se cuela, vuelve a la revisión anterior en segundos:

```bash
# Lista las revisiones recientes con sus nombres y distribución de tráfico — encuentra aquí el nombre de la última revisión buena.
gcloud run revisions list --service=mycoolproject --region=southamerica-east1

# Desvía el 100% del tráfico a una revisión específica, revirtiendo el sitio activo al instante.
# Reemplaza mycoolproject-<revisión-anterior> con el nombre de la revisión del comando anterior.
# Resultado: el sitio sirve inmediatamente la revisión anterior — no se necesita recompilación.
gcloud run services update-traffic mycoolproject \
  --region=southamerica-east1 \
  --to-revisions=mycoolproject-<revisión-anterior>=100
```

O vuelve a ejecutar el workflow de GitHub Actions del commit anterior — redespliega la imagen etiquetada con el SHA de ese commit.

---

## 📖 Navegación

- [01 — Configuración del Proyecto GCP](01_gcp_setup.md)
- [02 — Artifact Registry](02_artifact_registry.md)
- [03 — Cloud SQL (Base de datos PostgreSQL)](03_cloud_sql.md)
- [04 — Secret Manager](04_secret_manager.md)
- [05 — Cloud Storage (Media & static files)](05_cloud_storage.md)
- [06 — Dockerfile](06_dockerfile.md)
- [07 — Primer Despliegue](07_first_deploy.md)
- [08 — Dominio Personalizado y SSL](08_domain_ssl.md)
- [09 — Workload Identity Federation (Auth de GitHub sin llaves)](09_workload_identity.md)
- [10 — Pipeline CI/CD con GitHub Actions](10_github_actions.md)
- [11 — Referencia Rápida](11_quick_reference.md)
- [12 — Bonus: Email Personalizado (@dominio.cl)](12_custom_email.md)
