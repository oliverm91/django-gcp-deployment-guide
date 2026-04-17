---
description: "Aprende a crear un nuevo proyecto en Google Cloud Platform, habilitar APIs y configurar service accounts para un acceso seguro."
image: assets/social-banner.png

---
# 01 — Configuración del Proyecto GCP

> ✅ **Este capítulo es gratuito.** Crear proyectos, habilitar APIs y configurar service accounts no tiene costo.
>
> 💳 **Requiere una cuenta de facturación.** GCP requiere una tarjeta de crédito para crear una cuenta de facturación, incluso para usar servicios del nivel gratuito. Vincúlala en [console.cloud.google.com/billing](https://console.cloud.google.com/billing). Las cuentas nuevas reciben **$300 en créditos gratuitos** válidos por 90 días — suficiente para ejecutar toda esta infraestructura durante meses antes de pagar algo.

## ¿Qué es un proyecto de GCP?

Un proyecto de **Google Cloud Platform** (GCP) es un contenedor aislado para todos tus recursos en la nube — bases de datos, servidores, buckets de almacenamiento y facturación. Todo lo que crees en esta guía vive dentro de un solo proyecto. Puedes tener múltiples proyectos (por ejemplo, `mycoolproject-prod` y `mycoolproject-staging`) con recursos y facturación completamente separados.

## ¿Qué es el gcloud CLI?

`gcloud` es la herramienta de línea de comandos de Google para gestionar recursos de GCP. La ejecutas en tu terminal local. Se comunica con las APIs de GCP en tu nombre. Instálala desde [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install).

Todos los comandos a continuación se ejecutan **en tu terminal local** (no dentro de Django, no dentro de Docker). Usa bash, WSL2 o PowerShell según tu plataforma — `gcloud` funciona de manera idéntica en todas.

---

## Crear el proyecto

```bash
# Abre un navegador para autenticar tu gcloud CLI local con tu cuenta de Google.
# Requerido una vez por máquina antes de que cualquier otro comando de gcloud funcione.
# Resultado: gcloud imprime "You are now logged in as <email>"
gcloud auth login

# Crea un nuevo proyecto GCP llamado mycoolproject-prod.
# Todos los recursos (base de datos, contenedores, almacenamiento) vivirán dentro de este proyecto.
# Resultado: visible en console.cloud.google.com/home/dashboard?project=mycoolproject-prod
gcloud projects create mycoolproject-prod --name="MyCoolProject Prod"

# Establece mycoolproject-prod como el proyecto predeterminado para todos los comandos gcloud siguientes.
# Sin esto necesitarías agregar --project=mycoolproject-prod en cada comando.
gcloud config set project mycoolproject-prod

# Establece la región predeterminada para no necesitar --region= en cada comando.
# southamerica-east1 (São Paulo) es la región GCP más cercana a Chile.
gcloud config set run/region southamerica-east1
```

> **Región:** `southamerica-east1` es São Paulo — la región GCP más cercana a Chile (~30–60 ms de latencia a Santiago). Todos los recursos de esta guía usan esta región para consistencia.

---

## Habilitar APIs

Los servicios de GCP están deshabilitados por defecto — habilitás solo lo que necesitas. Este es un paso único por proyecto.

```bash
# Habilita todas las APIs de GCP que necesita este proyecto. Las APIs están deshabilitadas por defecto —
# nada funciona hasta que las habilites. Este es un paso único por proyecto.
# Resultado: cada API listada en console.cloud.google.com/apis/dashboard
gcloud services enable \
  run.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  artifactregistry.googleapis.com \
  storage.googleapis.com \
  iamcredentials.googleapis.com
```

Qué hace cada API:

| API | Habilita |
|---|---|
| `run.googleapis.com` | Cloud Run (ejecuta el contenedor Django) |
| `sqladmin.googleapis.com` | Cloud SQL (base de datos PostgreSQL) |
| `secretmanager.googleapis.com` | Secret Manager (almacenamiento de credenciales) |
| `artifactregistry.googleapis.com` | Artifact Registry (almacenamiento de imágenes Docker) |
| `storage.googleapis.com` | Cloud Storage (archivos media y static) |
| `iamcredentials.googleapis.com` | Workload Identity (autenticación de GitHub Actions sin claves) |

---

## Crear una Service Account

### ¿Qué es una Service Account?

Una service account es una identidad para un programa (no para una persona). En lugar de que tu contenedor de Cloud Run se ejecute como tú (el desarrollador), se ejecuta como una cuenta dedicada que solo tiene los permisos que necesita. Esto limita el radio de daño si la aplicación alguna vez se ve comprometida.

```bash
# Crea una service account — una identidad para que el contenedor de Cloud Run la use.
# Usar una cuenta dedicada (no tu cuenta personal) limita el radio de daño si se compromete.
# Resultado: visible en console.cloud.google.com/iam-admin/serviceaccounts
gcloud iam service-accounts create mycoolproject-run-sa \

  --display-name="MyCoolProject Cloud Run SA"
```

Esto crea la identidad `mycoolproject-run-sa@mycoolproject-prod.iam.gserviceaccount.com`.

### ¿Qué son los roles de IAM?

Los roles de IAM (Identity and Access Management) son conjuntos de permisos. Asignas roles a identidades (usuarios o service accounts). En lugar de dar acceso de administrador amplio, das solo lo necesario:

```bash
SA="mycoolproject-run-sa@mycoolproject-prod.iam.gserviceaccount.com"

# Otorga a la service account permiso para conectarse a Cloud SQL a través del socket proxy.
# Sin esto, el contenedor no puede acceder a la base de datos en tiempo de ejecución.
# Resultado: visible en console.cloud.google.com/iam-admin/iam (filtrar por service account)
gcloud projects add-iam-policy-binding mycoolproject-prod \

  --member="serviceAccount:$SA" \
  --role="roles/cloudsql.client"

# Otorga permiso para leer secrets de Secret Manager.
# Sin esto, Cloud Run no puede obtener DATABASE_URL, SECRET_KEY, etc. al arrancar.
gcloud projects add-iam-policy-binding mycoolproject-prod \

  --member="serviceAccount:$SA" \
  --role="roles/secretmanager.secretAccessor"

# Otorga permiso para leer y escribir objetos en los buckets de Cloud Storage.
# Necesario para collectstatic (escritura) y para servir archivos media subidos por usuarios (lectura).
gcloud projects add-iam-policy-binding mycoolproject-prod \

  --member="serviceAccount:$SA" \
  --role="roles/storage.objectAdmin"
```

El contenedor de Cloud Run usará esta service account en tiempo de ejecución — automáticamente tiene estos permisos sin ningún archivo de credenciales.

---

---

## 💡 Información Relacionada: Google Login

Si tu aplicación Django utiliza **Google Login** (Gmail), estas credenciales (`GOOGLE_CLIENT_ID` y `GOOGLE_CLIENT_SECRET`) se crean y obtienen desde este mismo proyecto en la consola de Google Cloud (**APIs & Services > Credentials**).

Una vez obtenidas, deberás almacenarlas de forma segura siguiendo los pasos del [Capítulo 04 — Secret Manager](04_secret_manager.es.md).

---

## 📖 Navegación

- 01 — Configuración del Proyecto GCP (Capítulo actual)
- [02 — Artifact Registry](02_artifact_registry.es.md)
- [03 — Cloud SQL (Base de datos PostgreSQL)](03_cloud_sql.es.md)
- [04 — Secret Manager](04_secret_manager.es.md)
- [05 — Cloud Storage (Media & static files)](05_cloud_storage.es.md)
- [06 — Dockerfile](06_dockerfile.es.md)
- [07 — Primer Despliegue](07_first_deploy.es.md)
- [08 — Dominio Personalizado y SSL](08_domain_ssl.es.md)
- [09 — Workload Identity Federation (Auth de GitHub sin llaves)](09_workload_identity.es.md)
- [10 — Pipeline CI/CD con GitHub Actions](10_github_actions.es.md)
- [11 — Referencia Rápida](11_quick_reference.es.md)
- [12 — Bonus: Email Personalizado (@dominio.cl)](12_custom_email.es.md)
- [13 — Bonus: Django Tasks](13_django_tasks.es.md)
