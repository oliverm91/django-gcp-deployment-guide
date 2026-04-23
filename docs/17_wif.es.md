---
description: "Configura Workload Identity Federation para que GitHub Actions pueda autenticarse en GCP de forma segura sin almacenar claves JSON."
image: assets/social-banner.png
---

# 16 — Workload Identity Federation

← [Anterior: 15 — Dominio personalizado y SSL](16_domain_ssl.es.md)

Workload Identity Federation permite a GitHub Actions autenticarse en GCP usando tokens de corta duración en lugar de claves JSON de larga duración. Esto es más seguro y no requiere gestión manual de credenciales.

---

## Por qué importa esto

Sin Workload Identity, GitHub Actions necesitaría un archivo de clave JSON almacenado como secreto de GitHub. Esta clave:
- Nunca expira
- Puede ser filtrada si el repo se ve comprometido
- Requiere rotación manual

Con Workload Identity, GitHub Actions obtiene un token de corta duración (válido ~1 hora) que intercambia por acceso a GCP. Sin credenciales permanentes almacenadas en ningún lugar.

---

## Cómo funciona

```
GitHub Actions workflow
    │
    ├── Solicita token OIDC del proveedor OIDC de GitHub
    │     (prueba: "Soy workflow en TU_ORG/TU_REPO en rama main")
    │
    ├── Intercambia token por token de acceso de corta duración a GCP
    │
    └── Usa el token de GCP para empujar imágenes y desplegar
```

El límite de seguridad clave: solo tu repo de GitHub específico puede impersonar tu service account de GCP.

---

## Configuración (ejecutar en terminal local)

### Paso 1: Crear el Workload Identity Pool

```bash
PROJECT_NUMBER=$(gcloud projects describe mycoolproject-prod --format='value(projectNumber)')

gcloud iam workload-identity-pools create github-pool \
  --location=global \
  --display-name="GitHub Actions Pool"
```

### Paso 2: Crear el Proveedor OIDC

```bash
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --display-name="GitHub provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

### Paso 3: Otorgar permiso a la service account

```bash
gcloud iam service-accounts add-iam-policy-binding \
  mycoolproject-run@mycoolproject-prod.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/YOUR_ORG/YOUR_REPO"
```

Reemplaza `YOUR_ORG/YOUR_REPO` con tu org de GitHub y nombre de repo (ej., `octocat/mycoolproject`).

### Paso 4: Obtener el nombre del recurso del proveedor

```bash
gcloud iam workload-identity-pools providers describe github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --format="value(name)"
```

La salida se ve así:
```
projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider
```

**Copia esta cadena completa** — la necesitas para los secretos de GitHub.

---

## Agregar Secretos de GitHub

En tu repo de GitHub: **Settings → Secrets and variables → Actions → New repository secret**

| Nombre del secreto | Valor |
|---|---|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | `projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider` |
| `GCP_SERVICE_ACCOUNT` | `mycoolproject-run@mycoolproject-prod.iam.gserviceaccount.com` |

---

## Terraform: Crear el Workload Identity pool (opcional)

Terraform puede crear el pool y el proveedor:

```hcl
# Workload Identity Pool
resource "google_iam_workload_identity_pool" "github" {
  workload_identity_pool_id = "github-pool"
}

# OIDC Provider
resource "google_iam_workload_identity_pool_provider" "github" {
  workload_identity_pool_id = google_iam_workload_identity_pool.github.workload_identity_pool_id
  workload_identity_pool_location = "global"

  display_name = "GitHub provider"
  description  = "GitHub Actions OIDC provider"

  attribute_mapping = {
    "google.subject"         = "assertion.sub"
    "attribute.repository"   = "assertion.repository"
  }

  oidc {
    issuer_uri = "https://token.actions.githubusercontent.com"
  }
}

# Grant the service account permission to impersonate
resource "google_service_account_iam_member" "run_workload_identity" {
  service_account_id = google_service_account.run.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${data.google_project.project.number}/locations/global/workloadIdentityPools/${google_iam_workload_identity_pool.github.workload_identity_pool_id}/attribute.repository/${var.github_repo}"
}
```

---

## Cómo GitHub Actions lo usa

En el workflow de GitHub Actions:

```yaml
- name: Authenticate to GCP
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
    service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}

- name: Set up gcloud
  uses: google-github-actions/setup-gcloud@v2

# Now gcloud and docker commands work
- docker build ...
- docker push ...
- gcloud run deploy ...
```

Después de este paso, todos los comandos `gcloud` y `docker push` en el workflow usan las credenciales autenticadas de GCP.

---

## Verificar que funciona

Haz push de un commit a main y observa el workflow de GitHub Actions. Si la autenticación funciona, deberías ver:

```
Authenticating to GCP with Workload Identity
gcloud credentials: OK
```

Si falla, verifica dos veces que los secretos `GCP_WORKLOAD_IDENTITY_PROVIDER` y `GCP_SERVICE_ACCOUNT` son correctos.

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
- 16 — Workload Identity Federation (Capítulo actual)
- [17 — GitHub Actions CI/CD](18_github_actions.es.md)
- [18 — Referencia Rápida](19_quick_reference.es.md)
