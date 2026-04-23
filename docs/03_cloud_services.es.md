---
description: "Comprende cada servicio en la nube que usamos: qué hace, cómo encaja en la arquitectura y los conceptos clave para el despliegue."
image: assets/social-banner.png
---

# 03 — Servicios en la nube explicados

← [Anterior: 02 — Visión general de Terraform](02_terraform_overview.es.md)

Este capítulo explica cada servicio en la nube que usaremos. La guía implementa esta infraestructura en **Google Cloud Platform (GCP)**, pero los conceptos aplican a través de proveedores de nube.

---

## Vista general de la plataforma en la nube

Una plataforma en la nube proporciona cómputo, almacenamiento, bases de datos, redes y más — cada servicio es independiente y se gestiona a través de Terraform o la consola del proveedor.

Usaremos un subconjunto de estos servicios. Repasemos cada uno.

---

## Cloud Run

### Qué es

Cloud Run es una **plataforma de contenedores sin servidor**. Le das una imagen Docker y ejecuta un servicio que:
- Inicia cuando llegan solicitudes
- Escala a cero cuando está inactivo (sin costo)
- Escala automáticamente bajo carga
- Maneja HTTPS automáticamente
- Te da una URL pública

### Por qué lo usamos

En lugar de gestionar VMs o clusters de Kubernetes, solo despliegas una imagen Docker y Cloud Run maneja todo lo demás. Es la forma más simple de ejecutar una aplicación web en producción en GCP.

### Conceptos clave

- **Service** — la aplicación web en ejecución. Tiene una URL, historial de revisiones, división de tráfico.
- **Revision** — una versión específica del servicio (creada en cada despliegue).
- **Container** — una instancia en ejecución de tu imagen Docker.
- **Concurrency** — cuántas solicitudes maneja cada contenedor simultáneamente.

### Costo

Nivel gratuito: 2 millones de solicitudes + 360K segundos de CPU GB por mes.
Después de eso: ~$0.00004 por solicitud.

Con `--min-instances=0` (escala a cero), no pagas nada cuando no hay tráfico.

---

## Cloud Tasks

### Qué es

Cloud Tasks es una **cola de tareas gestionada**. Encolas un trabajo (una unidad de trabajo) y un worker lo recoge y procesa. Piénsalo como una lista de tareas para trabajo en segundo plano.

### Por qué lo usamos

Algunas operaciones son demasiado lentas o pesadas para ejecutar dentro de una solicitud web:
- Envío de emails (puede tomar segundos)
- Generación de PDFs o reportes
- Procesamiento de imágenes
- Llamadas a APIs externas que son lentas

En lugar de hacer esperar al usuario, encolas el trabajo y respondes inmediatamente. El worker lo procesa en segundo plano.

### Conceptos clave

- **Queue** — una cola nombrada que contiene tareas. Crearemos una llamada `default`.
- **Task** — una unidad de trabajo (esencialmente una llamada a función con argumentos, serializada).
- **Worker** — un Job separado de Cloud Run que extrae tareas de la cola y las procesa.

### Cómo funciona

```
Solicitud web → Django la recibe → Encola tarea a Cloud Tasks →
Django responde inmediatamente (el usuario no espera) →
Worker de Cloud Run Job recoge la tarea → Hace el trabajo
```

### ¿Por qué no Cloud Run Jobs directamente?

Cloud Run Jobs se ejecutan una vez y terminan. Cloud Tasks proporciona:
- **Fiabilidad** — si un worker falla, Cloud Tasks reintenta la tarea
- **Programación** — las tareas de Cloud Tasks pueden programarse para ejecutarse en un momento específico (útil para recordatorios, trabajos por lotes)
- **Límite de tasa** — previene que tus workers se vean abrumados
- **Gestión de cola** — pausar, reanudar, purgar colas

Cloud Run Jobs es lo que realmente **ejecuta** las tareas. Cloud Tasks es la **cola** que las contiene.

---

## Cloud Scheduler

### Qué es

Cloud Scheduler es un **servicio cron** — activa algo en un horario basado en tiempo.

### Por qué lo usamos

Necesitamos activar el worker de Cloud Tasks periódicamente. Cloud Scheduler puede hacer POST a un endpoint en un horario, lo que activa el worker para procesar cualquier tarea pendiente.

Por ejemplo: "verificar cada minuto si hay tareas pendientes" o "enviar resumen diario a las 9am".

### Cómo funciona

```
Cloud Scheduler (cada minuto)
    │
    ▼
POST a la URL del Cloud Run Job → Worker despierta → Procesa tareas pendientes
```

Cloud Scheduler en sí es un mecanismo de activación — el trabajo real lo hacen los Cloud Run Jobs.

---

## Cloud Storage (GCS)

### Qué es

Cloud Storage es el **almacenamiento de objetos** de Google — como AWS S3. Los archivos se almacenan como objetos en buckets (espacios de nombres planos, no directorios). Es duradero, accesible globalmente y barato.

### Por qué lo usamos

Dos razones:

1. **Archivos estáticos** — CSS, JavaScript, íconos. Estos se generan con `collectstatic` y se suben a un bucket de GCS. Los navegadores los cargan directamente desde GCS, no desde Django.

2. **Archivos media** — imágenes subidas por usuarios (avatares, fotos). Almacenadas en GCS, no en el sistema de archivos del contenedor (que se perdería si el contenedor se reinicia).

### Conceptos clave

- **Bucket** — un contenedor para objetos. Los nombres de bucket son únicos globalmente.
- **Object** — un archivo almacenado en un bucket.
- **Acceso público** — los buckets pueden ser públicos (cualquiera puede leer) o privados.

### Dos buckets

| Bucket | Propósito | Acceso |
|---|---|---|
| `my-project-static` | CSS, JS, íconos de `collectstatic` | Público |
| `my-project-media` | Subidas de usuarios (imágenes) | Público |

El acceso público significa que los navegadores pueden cargar assets estáticos directamente desde GCS, evitando completamente a Django.

---

## Artifact Registry

### Qué es

Artifact Registry es el **registro de contenedores privado** de GCP — un lugar para almacenar imágenes Docker. Piénsalo como Docker Hub, pero dentro de tu proyecto de GCP y privado.

### Por qué lo usamos

Cuando GitHub Actions construye tu imagen Docker, necesita un lugar para almacenarla. Cloud Run extrae de aquí al desplegar. La imagen nunca sale de la red de GCP.

### Conceptos clave

- **Repository** — una colección de imágenes relacionadas (tenemos una llamada `my-project-repo`)
- **Image** — la imagen Docker real con una etiqueta (ej., `app:latest`, `app:<git-sha>`)
- **Tags** — etiquetas como `latest` o `abc123` que apuntan a imágenes específicas

### Nombres de imágenes

Las imágenes en Artifact Registry se ven así:
```
southamerica-east1-docker.pkg.dev/my-project/my-project-repo/app:latest
```

Desglose:
- `southamerica-east1-docker.pkg.dev` — el host del registro
- `my-project` — tu proyecto de GCP
- `my-project-repo` — el nombre del repositorio
- `app` — el nombre de la imagen
- `latest` — la etiqueta

---

## Secret Manager

### Qué es

Secret Manager almacena **secretos** — contraseñas, claves API, tokens, cualquier cosa sensible. Los secretos están encriptados en reposo y solo se desencriptan cuando se solicitan.

### Por qué lo usamos

No podemos hardcodear credenciales en el código ni ponerlas en archivos de entorno que se comprometen a git. Secret Manager proporciona:
- Encriptación en reposo
- Historial de versiones (revertir si es necesario)
- Control de acceso vía IAM
- Inyección en tiempo de ejecución en Cloud Run

### Cómo funciona con Cloud Run

Al desplegar en Cloud Run, referencias secretos por nombre. Al iniciar el contenedor, Cloud Run obtiene los valores de los secretos y los inyecta como variables de entorno.

```bash
--set-secrets=DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=SECRET_KEY:latest
```

Esto mapea el secreto de Secret Manager `DATABASE_URL` a la variable de entorno `DATABASE_URL` dentro del contenedor.

### Costo

Nivel gratuito: 6 versiones de secretos y 10,000 accesos por mes.
Después de eso: $0.06 por versión por mes.

---

## IAM (Gestión de Identidad y Acceso)

### Qué es

IAM controla **quién puede hacer qué** en tu proyecto de GCP. Funciona con:
- **Members** — usuarios, service accounts, grupos
- **Roles** — conjuntos de permisos (como "puede leer buckets de storage")
- **Policies** — adjuntar roles a miembros

### Por qué lo usamos

En lugar de dar a todos acceso de administrador, seguimos el principio de mínimo privilegio: dar a cada identidad solo los permisos que necesita.

### Service Accounts

Una **service account** es una identidad para un programa (no para una persona). Nuestros contenedores de Cloud Run se ejecutan como una service account, que tiene permisos para:
- Leer secretos de Secret Manager
- Leer/escribir objetos en Cloud Storage
- Conectarse a PlanetScale (vía cadena de conexión — no es específico de GCP)

### Ejemplo

```bash
# Dar a la service account de Cloud Run permiso para leer secretos
gcloud projects add-iam-policy-binding my-project \
  --member="serviceAccount:my-run-sa@my-project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

En Terraform:

```hcl
resource "google_project_iam_member" "run_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.run.email}"
}
```

---

## Lo que NO usamos (y por qué)

### Cloud SQL

Usamos PlanetScale en lugar de Cloud SQL de GCP porque:
- PlanetScale tiene un nivel de desarrollo gratuito
- Sin servidor (sin gestión de servidores)
- Las ramas de base de datos son excelentes para el flujo de trabajo (rama para feature, fusionar, desplegar)
- Precio más simple

Si necesitas características completas de Postgres (como restricciones de clave foránea), podrías usar Cloud SQL de GCP en su lugar — requiere gestionar el servidor de base de datos tú mismo, pero ofrece compatibilidad completa con Postgres.

### Kubernetes (GKE)

Kubernetes es más poderoso pero significativamente más complejo. Cloud Run es más simple para nuestro caso de uso — maneja escalado, redes y SSL automáticamente. No necesitamos el control que Kubernetes proporciona.

### Balanceador de carga

Cloud Run maneja HTTPS y enrutamiento automáticamente. No necesitamos un balanceador de carga separado.

---

## Navegación



- [01 — Introduction: What We're Building](01_introduction.es.md)
- [02 — Terraform Overview](02_terraform_overview.es.md)
- 03 — Cloud Services Explained (Capítulo actual)
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