---
description: "Almacena credenciales, claves API y cadenas de conexión en GCP Secret Manager usando Terraform."
image: assets/social-banner.png
---

# 08 — Gestión de Secretos

← [Anterior: 07 — Artifact Registry](07_artifact_registry.es.md)

Secret Manager almacena valores sensibles como contraseñas, claves API y cadenas de conexión. En este capítulo, crearemos secretos con Terraform y almacenaremos los valores reales vía CLI.

---

## ¿Por qué Secret Manager?

Antes de Secret Manager, los equipos ponían secretos en:
- Variables de entorno (visibles en logs, texto plano en consola)
- Archivos `.env` (comprometidos a git accidentalmente, filtrados)
- Código (peor — visible en el historial de código)

Secret Manager proporciona:
- Encriptación en reposo
- Historial de versiones
- Control de acceso vía IAM
- Inyección en tiempo de ejecución en Cloud Run

### Terraform vs. manual: quién hace qué?

Terraform define la **estructura** — qué secretos existen, sus nombres, configuraciones de replicación. Los **valores reales** (contraseñas, claves API, cadenas de conexión) se establecen por separado y nunca se almacenan en el estado de Terraform.

Esto es intencional: los archivos de estado de Terraform se almacenan en control de versiones o almacenamiento en la nube, y almacenar valores de secretos en el estado sería un riesgo de seguridad. En cambio:

- **Terraform** crea el contenedor del secreto
- **Tú** estableces el valor vía CLI (o pipeline CI/CD)
- **Cloud Run** lee el valor en tiempo de ejecución

---

## Crear secretos con Terraform

Agrega a `infrastructure/main.tf`:

```hcl
# Secret Manager secrets
resource "google_secret_manager_secret" "database_url" {
  secret_id = "DATABASE_URL"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "django_secret_key" {
  secret_id = "DJANGO_SECRET_KEY"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "google_client_id" {
  secret_id = "GOOGLE_CLIENT_ID"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "google_client_secret" {
  secret_id = "GOOGLE_CLIENT_SECRET"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "email_host" {
  secret_id = "EMAIL_HOST"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "email_port" {
  secret_id = "EMAIL_PORT"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "email_host_user" {
  secret_id = "EMAIL_HOST_USER"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "email_host_password" {
  secret_id = "EMAIL_HOST_PASSWORD"
  replication {
    auto {}
  }
}
```

Ejecuta `terraform apply` para crear la estructura de secretos.

---

## Establecer valores de secretos (vía CLI, no Terraform)

Terraform puede almacenar la *estructura del secreto* pero **no** los valores reales — los secretos se establecen en tiempo de ejecución, no se incluyen en el estado. Usa la CLI de `gcloud` para establecer cada secreto:

```bash
# Database URL (from PlanetScale)
echo -n "postgres://user:password@aws.connect.psdb.cloud/mycoolproject?sslmode=require" \
  | gcloud secrets versions add DATABASE_URL --data-file=-

# Django secret key (generate a random one)
python -c "import secrets; print(secrets.token_urlsafe(50))"
# Copy the output and use it:
echo -n "<your-generated-secret-key>" \
  | gcloud secrets versions add DJANGO_SECRET_KEY --data-file=-

# Google OAuth credentials (from Google Cloud Console)
echo -n "<your-google-client-id>" \
  | gcloud secrets versions add GOOGLE_CLIENT_ID --data-file=-

echo -n "<your-google-client-secret>" \
  | gcloud secrets versions add GOOGLE_CLIENT_SECRET --data-file=-

# Email (SMTP credentials from your email provider)
echo -n "smtp.sendgrid.net" \
  | gcloud secrets versions add EMAIL_HOST --data-file=-

echo -n "587" \
  | gcloud secrets versions add EMAIL_PORT --data-file=-

echo -n "<your-smtp-username>" \
  | gcloud secrets versions add EMAIL_HOST_USER --data-file=-

echo -n "<your-smtp-password>" \
  | gcloud secrets versions add EMAIL_HOST_PASSWORD --data-file=-
```

### Generar una clave secreta de Django

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Esto genera una cadena aleatoria criptográficamente segura adecuada para la `SECRET_KEY` de Django.

---

## Cómo Cloud Run usa los secretos

Cuando despleguemos en Cloud Run más adelante, mapeamos secretos a variables de entorno:

```bash
--set-secrets=DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=DJANGO_SECRET_KEY:latest
```

Esto le dice a Cloud Run: "Busca la última versión de `DATABASE_URL` de Secret Manager e inyéctala como la variable de entorno `DATABASE_URL` dentro del contenedor."

---

## IAM: Permitir a Cloud Run leer secretos

Necesitamos otorgar a la service account permiso para leer secretos. Crearemos la service account en el siguiente capítulo, pero aquí está el Terraform:

```hcl
# Allow Cloud Run service account to read all our secrets
resource "google_secret_manager_secret_iam_binding" "run_secret_accessor" {
  secret_id = google_secret_manager_secret.database_url.secret_id
  role     = "roles/secretmanager.secretAccessor"
  members  = ["serviceAccount:${google_service_account.run.email}"]
}

# Repeat for other secrets, or use a project-level policy
resource "google_project_iam_member" "run_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.run.email}"
}
```

Usar `google_project_iam_member` con `roles/secretmanager.secretAccessor` a nivel de proyecto es más fácil — otorga acceso a todos los secretos en el proyecto.

---

## Verificar que los secretos existen

```bash
gcloud secrets list
```

Deberías ver todos los secretos que creamos.

---

## Actualizar un secreto (para rotación)

```bash
echo -n "new-value" | gcloud secrets versions add SECRET_NAME --data-file=-
```

La etiqueta `latest` siempre apunta a la versión más nueva. Cloud Run recoge el nuevo valor en el próximo reinicio del contenedor o nuevo despliegue.

---

## Navegación



- [01 — Introducción: Qué vamos a construir](01_introduction.es.md)
- [02 — Visión general de Terraform](02_terraform_overview.es.md)
- [03 — Servicios en la nube explicados](03_cloud_services.es.md)
- [04 — Base de datos PlanetScale explicada](04_planetscale.es.md)
- [05 — Configuración del proyecto y estado de Terraform](05_project_setup.es.md)
- [06 — Proyecto GCP y APIs](06_gcp_project.es.md)
- [07 — Artifact Registry](07_artifact_registry.es.md)
- 08 — Gestión de Secretos (Capítulo actual)
- [09 — Cloud Storage](10_storage.es.md)
- [10 — Service Accounts e IAM](11_iam.es.md)
- [11 — Cloud Run](12_cloud_run.es.md)
- [12 — Trabajos en segundo plano y Scheduler](13_tasks.es.md)
- [13 — Dockerfile](14_dockerfile.es.md)
- [14 — Primer Despliegue](15_first_deploy.es.md)
- [15 — Dominio personalizado y SSL](16_domain_ssl.es.md)
- [16 — Workload Identity Federation](17_wif.es.md)
- [17 — GitHub Actions CI/CD](18_github_actions.es.md)
- [18 — Referencia Rápida](19_quick_reference.es.md)
