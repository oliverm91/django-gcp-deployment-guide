---
description: "Configura tu entorno local para Terraform, inicializa tu proyecto y configura el almacenamiento de estado remoto en GCP."
image: assets/social-banner.png
---

# 05 — Configuración del proyecto y estado de Terraform

← [Anterior: 04 — Base de datos PlanetScale explicada](04_planetscale.es.md)

Antes de escribir cualquier configuración de Terraform, necesitamos configurar la estructura del proyecto y entender dónde Terraform almacena su estado.

---

## El directorio del proyecto

Necesitamos un directorio para los archivos de Terraform. Dentro de tu proyecto Django, crea un directorio `infrastructure/`:

```bash
cd mycoolproject
mkdir -p infrastructure
cd infrastructure
```

Aquí es donde vivirán todos los archivos de Terraform. La estructura:

```
mycoolproject/
├── web/                    # App Django
│   ├── core/
│   ├── accounts/
│   └── ...
├── infrastructure/         # Archivos de Terraform (enfoque de esta guía)
│   ├── main.tf
│   ├── variables.tf
│   ├── terraform.tfvars    # NO comprometido a git
│   ├── .terraform/
│   └── terraform.tfstate   # Local por ahora (remoto después)
└── .github/
    └── workflows/
```

---

## El problema del archivo de estado

Terraform necesita recordar lo que creó. Lo hace en un **archivo de estado** (`terraform.tfstate`).

Si trabajas solo, puedes almacenarlo localmente. Pero si trabajas con un equipo o quieres destruir y recrear infraestructura de forma confiable, el estado necesita almacenarse de forma remota — en Cloud Storage de GCP.

### ¿Por qué estado remoto?

- **Colaboración en equipo** — todos leen el mismo estado
- **Bloqueo** — previene que applies concurrentes rompan cosas
- **Durabilidad** — sobrevive a que se pierda o reformatee tu laptop

### Crear un bucket de GCS para el estado de Terraform

Crearemos este bucket manualmente (es el problema del huevo y la gallina: Terraform necesita estado, pero necesitamos Terraform para crear infraestructura para almacenar estado). Así que creamos el bucket con `gcloud`, luego configuramos Terraform para usarlo.

Ejecuta esto **una vez** desde tu terminal local:

```bash
# Crear un bucket de GCS para almacenar el estado de Terraform
# El estado debe vivir en un bucket único — usa el nombre de tu proyecto y un sufijo
gsutil mb -l southamerica-east1 gs://mycoolproject-terraform-state

# Habilitar versionado para poder recuperar estados anteriores si es necesario
gsutil versioning set on gs://mycoolproject-terraform-state

# Verificar que existe
gsutil ls
```

Ahora tenemos dónde almacenar el estado. Pero necesitamos que Terraform mismo cree el resto de la infraestructura — así que inicializamos Terraform primero con estado local, luego migramos a estado remoto.

---

## Crear los archivos de configuración de Terraform

Crea `infrastructure/variables.tf`:

```hcl
variable "project_id" {
  type        = string
  description = "El ID del proyecto GCP"
}

variable "region" {
  type        = string
  description = "Región GCP para todos los recursos"
  default     = "southamerica-east1"
}

variable "project_number" {
  type        = string
  description = "El número del proyecto GCP"
}
```

Crea `infrastructure/terraform.tfvars` (ejemplo — reemplaza con tus valores):

```hcl
project_id    = "mycoolproject-prod"
region        = "southamerica-east1"
```

Crea `infrastructure/main.tf`:

```hcl
terraform {
  required_version = ">= 1.5.0"

  # Estado local por ahora — cambiaremos a remoto después del primer apply
  # Descomenta el bloque backend más adelante para usar GCS
  # backend "gcs" {
  #   bucket = "mycoolproject-terraform-state"
  #   prefix = "terraform/state"
  # }
}

provider "google" {
  project = var.project_id
  region  = var.region
}
```

---

## Inicializar Terraform

```bash
cd infrastructure
terraform init

# Deberías ver:
# - Initializing provider plugins...
# - Terraform has been successfully initialized!
```

Esto descarga el plugin del provider de GCP y configura el directorio de trabajo.

---

## Plan y apply

### Obtener tu número de proyecto

Terraform necesita el número del proyecto (diferente del ID del proyecto). Obténlo:

```bash
gcloud projects describe mycoolproject-prod --format='value(projectNumber)'
```

Usa este valor en tu `terraform.tfvars`:

```hcl
project_id      = "mycoolproject-prod"
region          = "southamerica-east1"
project_number  = "123456789012"  # Reemplaza con tu número real
```

### Ejecutar terraform plan

```bash
terraform plan
```

Esto muestra qué creará Terraform. Como solo tenemos el provider y aún no hay recursos, dirá "No changes."

### Almacenar estado en GCS (después de confirmar que funciona)

Una vez que tengas recursos, migra a estado remoto:

```hcl
# Descomenta el bloque backend en main.tf
terraform {
  backend "gcs" {
    bucket = "mycoolproject-terraform-state"
    prefix = "terraform/state"
  }
}
```

Luego migra:

```bash
terraform init -migrate-state
```

---

## Estructura del directorio para el resto de esta guía

En los siguientes capítulos, agregaremos recursos a `main.tf` incrementalmente. Por ahora, comienza con esta estructura:

```
infrastructure/
├── main.tf           # Vacío (provider + backend)
├── variables.tf      # Declaraciones de variables
├── terraform.tfvars  # Valores reales (no en git)
└── .terraform/       # Plugins de providers (auto-generado)
```

---

## Importante: terraform.tfvars

El archivo `terraform.tfvars` contiene valores reales — ID del proyecto, región, y eventualmente secretos. **Nunca comprometas este archivo a git.** Agrégalo a `.gitignore`:

```bash
echo "infrastructure/terraform.tfvars" >> .gitignore
```

Las declaraciones de variables van en `variables.tf` (que SÍ se compromete). Los valores reales van en `terraform.tfvars` (que NO se compromete).

---

## Navegación



- [01 — Introduction: What We're Building](01_introduction.es.md)
- [02 — Terraform Overview](02_terraform_overview.es.md)
- [03 — Cloud Services Explained](03_cloud_services.es.md)
- [04 — PlanetScale Database Explained](04_planetscale.es.md)
- 05 — Project Setup & Terraform State (Capítulo actual)
- [06 — GCP Project & APIs](06_gcp_project.es.md)
- [07 — Artifact Registry](07_artifact_registry.es.md)
- [08 — Secrets Management](09_secrets.es.md)
- [09 — Cloud Storage](10_storage.es.md)
- [10 — Service Accounts & IAM](11_iam.es.md)
- [11 — Cloud Run](12_cloud_run.es.md)
- [12 — Cloud Tasks & Scheduler](13_tasks.es.md)
- [13 — Dockerfile](14_dockerfile.es.md)
- [14 — First Deploy](15_first_deploy.es.md)
- [15 — Custom Domain & SSL](16_domain_ssl.es.md)
- [16 — Workload Identity Federation](17_wif.es.md)
- [17 — GitHub Actions CI/CD](18_github_actions.es.md)
- [18 — Quick Reference](19_quick_reference.es.md)