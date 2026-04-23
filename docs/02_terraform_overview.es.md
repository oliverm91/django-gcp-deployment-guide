---
description: "Comprende qué es Terraform, cómo funciona y los conceptos clave que necesitas para usarlo efectivamente."
image: assets/social-banner.png
---

# 02 — Visión general de Terraform

← [Anterior: 01 — Introducción: Qué vamos a construir](01_introduction.es.md)

Si nunca has usado Terraform antes, este capítulo te da todo lo que necesitas saber sobre cómo funciona antes de empezar a escribir archivos de configuración.

---

## ¿Qué es Terraform?

Terraform es una herramienta de **Infraestructura como Código (IaC)** creada por HashiCorp. En lugar de hacer clic en una consola web o ejecutar comandos CLI, escribes archivos de configuración que describen la infraestructura que quieres. Terraform entonces crea, actualiza y destruye recursos para igualarlos.

Piénsalo como una receta: describes el plato, Terraform hace la cocina.

**¿Por qué no usar solo comandos `gcloud`?**

- Los comandos `gcloud` son imperativos — "haz esta cosa ahora"
- Terraform es declarativo — "esto es lo que quiero que se vea el mundo"

Con herramientas imperativas, tienes que recordar los pasos y el orden. Con Terraform, solo describes el estado final deseado y él descubre cómo llegar allí.

---

## Conceptos fundamentales

### Providers

Un **provider** es un plugin que Terraform usa para interactuar con un servicio específico. Para esta guía usamos:

- `google` — el provider de GCP (crea recursos de GCP)
- `hashicorp/random` — genera valores aleatorios (útil para nombres únicos)
- `hashicorp/local` — trabaja con archivos locales

Los providers se definen al inicio de tus archivos de Terraform. Verás algo como:

```hcl
provider "google" {
  project = "my-project"
  region  = "southamerica-east1"
}
```

Esto le dice a Terraform: "Estoy trabajando con GCP, el proyecto es `my-project`, la región predeterminada es `southamerica-east1`."

### PlanetScale: gestionado manualmente

Las bases de datos y ramas de PlanetScale se crean y gestionan a través del dashboard o CLI de PlanetScale — no a través de Terraform. Terraform se usa para toda la infraestructura de GCP. La cadena de conexión de la base de datos se almacena en Secret Manager (creado por Terraform) y el valor se establece manualmente.

### Resources

Un **resource** es un elemento de infraestructura que Terraform gestiona. Ejemplos: un servicio de Cloud Run, un bucket de Storage, un secreto de Secret Manager.

Los recursos se ven así:

```hcl
resource "google_storage_bucket" "static" {
  name     = "my-project-static"
  location = "southamerica-east1"
}
```

Esto dice: "Crear un recurso del tipo `google_storage_bucket` llamado `static`. Establecer su `name` en `my-project-static` y `location` en `southamerica-east1`."

La primera parte (`google_storage_bucket`) le dice a Terraform qué provider usar. La segunda parte (`static`) es solo un nombre que usas para referenciar este recurso dentro de tu código de Terraform.

### Variables

Las **variables** te permiten parametrizar tu configuración de Terraform. En lugar de hardcodear valores, los defines una vez y los reutilizas:

```hcl
variable "project_id" {
  type        = string
  description = "El ID del proyecto GCP"
}
```

Luego usas `var.project_id` en cualquier lugar donde necesites ese valor. Esto hace tus archivos de Terraform más flexibles y reutilizables.

### Valores de salida

Los **outputs** imprimen valores útiles después de que `terraform apply` completa. Se usan frecuentemente para mostrar URLs o cadenas de conexión:

```hcl
output "bucket_url" {
  value = "https://storage.googleapis.com/${google_storage_bucket.static.name}"
}
```

---

## El flujo de trabajo

### 1. Escribir configuración

Crea archivos `.tf` que describan tu infraestructura. Comienza con el provider y los recursos.

### 2. Inicializar

```bash
terraform init
```

Esto descarga los plugins de los providers y configura el directorio de trabajo.

### 3. Plan

```bash
terraform plan
```

Terraform muestra qué creará, actualizará o destruirá — antes de hacer cualquier cambio real. Revisa esta salida cuidadosamente.

### 4. Aplicar

```bash
terraform apply
```

Terraform crea o actualiza recursos para igualar tu configuración. Escribe `yes` cuando se te pida.

### 5. Inspeccionar el estado

```bash
terraform show          # Ver el estado actual
terraform state list    # Listar todos los recursos
```

---

## Estado

Terraform almacena lo que creó en un **archivo de estado**. Así es como sabe qué es real versus lo que está en tus archivos de configuración.

### Estado local vs remoto

- **Estado local** — almacenado en tu laptop (riesgoso para equipos, se pierde si la laptop muere)
- **Estado remoto** — almacenado en almacenamiento en la nube (bucket de GCS), compartido entre el equipo

Para esta guía, almacenamos el estado en un bucket de Cloud Storage de GCP para que todos en el equipo usen el mismo estado.

### Consejos sobre archivos de estado

- **Nunca edites el estado manualmente** — deja que Terraform lo gestione
- **Almacena el estado de forma remota** — especialmente cuando trabajas en equipo
- **El estado contiene valores sensibles** — muestra nombres reales de recursos, a veces IDs

---

## Módulos

Los **módulos** son plantillas de Terraform reutilizables. En lugar de copiar las mismas definiciones de recursos entre proyectos, los empaquetas como un módulo.

Para esta guía, mantenemos las cosas simples y escribimos Terraform directamente en `main.tf`. A medida que crezcas, podrías extraer patrones comunes en módulos.

---

## Instalar Terraform

Si aún no has instalado Terraform:

```bash
# macOS (Homebrew)
brew install terraform

# Linux
curl -fsSL https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list
apt update && apt install terraform

# Windows: descarga desde terraform.io/downloads y agrégalo a PATH

# Verificar
terraform --version
```

---

## Navegación



- [01 — Introduction: What We're Building](01_introduction.es.md)
- 02 — Terraform Overview (Capítulo actual)
- [03 — Cloud Services Explained](03_cloud_services.es.md)
- [04 — PlanetScale Database Explained](04_planetscale.es.md)
- [05 — Project Setup & Terraform State](05_project_setup.es.md)
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