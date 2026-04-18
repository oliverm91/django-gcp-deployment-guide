---
description: "Almacena de forma segura variables de entorno, contraseñas y Django SECRET_KEYs usando GCP Secret Manager."
image: assets/social-banner.png

---
# 04 — Secret Manager

← [Anterior: 03 — Cloud SQL (Base de Datos PostgreSQL)](03_cloud_sql.md)

> ✅ **Prácticamente gratuito.** El nivel gratuito incluye 6 versiones de secrets y 10.000 operaciones de acceso por mes. Este proyecto almacena ~11 secrets, lo que supera las 6 versiones gratuitas — el costo es de $0.06/versión/mes, aproximadamente **$0.66/mes** en total (11 secrets × $0.06). Cada arranque de contenedor accede a los secrets una vez; con tráfico bajo esto se mantiene dentro de la cuota gratuita de acceso.

## ¿Qué es Secret Manager?

Secret Manager es el servicio de GCP para almacenar y acceder a valores sensibles: contraseñas, API keys, claves privadas. En lugar de poner credenciales en archivos `.env` en un servidor o hardcodearlas, las almacenas aquí y la aplicación las obtiene en tiempo de ejecución.

## ¿Por qué no usar simplemente variables de entorno?

Puedes establecer variables de entorno directamente en Cloud Run, pero aparecen en texto plano en la consola de GCP y en los logs de despliegue. Secret Manager cifra los valores en reposo, controla el acceso via IAM y mantiene un historial de versiones para que puedas revertir un cambio de secret.

## ¿Cómo recibe Django los secrets?

En el comando de despliegue de Cloud Run, los secrets se mapean a variables de entorno usando `--set-secrets`. Al arrancar el contenedor, Cloud Run obtiene los valores de los secrets de Secret Manager y los inyecta como variables de entorno. Django los lee a través de `django-environ` de la misma forma en que lee un archivo `.env`.

Por ejemplo, `--set-secrets=SECRET_KEY=DJANGO_SECRET_KEY:latest` hace que el secret llamado `DJANGO_SECRET_KEY` esté disponible como la variable de entorno `SECRET_KEY` dentro del contenedor.

---

## Almacenar todos los secrets

Ejecuta en tu **terminal local**.

> **Nota de plataforma:** Los ejemplos a continuación usan `echo -n` (sintaxis de bash/Linux/Mac). En **Windows PowerShell**, reemplaza `echo -n "valor" | gcloud secrets create ...` con:
> ```powershell
> "valor" | gcloud secrets create NOMBRE_SECRET --data-file=-
> ```
> O usa WSL2/Git Bash para mayor consistencia. **A partir de aquí, todos los ejemplos muestran sintaxis Linux/Mac.**

La pipe con `echo -n` pasa el valor sin un salto de línea al final:

```bash
# Cada comando a continuación pasa un valor via stdin (echo -n evita un salto de línea al final que
# corrompería el secret) y crea un secret con nombre en Secret Manager.
# --data-file=- significa "leer el valor desde stdin en lugar de un archivo".
# Resultado: todos los secrets visibles en console.cloud.google.com/security/secret-manager

# URL de conexión PostgreSQL (construida en el capítulo 03)
echo -n "postgresql://djangouser:<contraseña>@/mycoolproject?host=/cloudsql/mycoolproject-prod:southamerica-east1:mycoolproject-db" \
  | gcloud secrets create DATABASE_URL --data-file=-

# Django secret key — usada para firmar cookies y tokens CSRF. Debe ser larga y aleatoria.
# Genera con: python -c "import secrets; print(secrets.token_urlsafe(50))"
echo -n "<tu-django-secret-key>" \
  | gcloud secrets create DJANGO_SECRET_KEY --data-file=-

# Credenciales OAuth de Google — desde Google Cloud Console → APIs & Services → Credenciales
echo -n "<google-client-id>"     | gcloud secrets create GOOGLE_CLIENT_ID --data-file=-
echo -n "<google-client-secret>" | gcloud secrets create GOOGLE_CLIENT_SECRET --data-file=-

# Credenciales SMTP para email transaccional (por ejemplo, Brevo, SendGrid o Gmail App Password)
echo -n "<smtp-host>"     | gcloud secrets create EMAIL_HOST --data-file=-
echo -n "587"             | gcloud secrets create EMAIL_PORT --data-file=-
echo -n "<smtp-user>"     | gcloud secrets create EMAIL_HOST_USER --data-file=-
echo -n "<smtp-password>" | gcloud secrets create EMAIL_HOST_PASSWORD --data-file=-

# Didit KYC — credenciales para el servicio de verificación de identidad
echo -n "<didit-api-key>"        | gcloud secrets create DIDIT_API_KEY --data-file=-
echo -n "<didit-workflow-id>"    | gcloud secrets create DIDIT_WORKFLOW_ID --data-file=-
echo -n "<didit-webhook-secret>" | gcloud secrets create DIDIT_WEBHOOK_SECRET --data-file=-
```

## Actualizar un secret

Cada actualización crea una nueva versión. El alias `latest` siempre apunta a la más reciente:

```bash
# Agrega una nueva versión a un secret existente. La versión anterior se conserva (no se elimina).
# Cloud Run toma el nuevo valor en el próximo reinicio del contenedor / nuevo despliegue.
echo -n "nuevo-valor" | gcloud secrets versions add NOMBRE_SECRET --data-file=-
```

El contenedor de Cloud Run en ejecución no tomará el nuevo valor hasta que se reinicie. Activa un nuevo despliegue para aplicar una rotación de secret.

## Verificar los secrets almacenados

```bash
# Lista todos los nombres de secrets del proyecto (los valores no se muestran).
gcloud secrets list

# Lista todas las versiones almacenadas de un secret — útil para confirmar que una actualización fue exitosa.
gcloud secrets versions list DATABASE_URL

# Imprime el valor de un secret en el terminal — usa con cuidado, evitar en sesiones compartidas.
gcloud secrets versions access latest --secret=DATABASE_URL
```

---

## 📖 Navegación

- [01 — Configuración del Proyecto GCP](01_gcp_setup.es.md)
- [02 — Artifact Registry](02_artifact_registry.es.md)
- [03 — Cloud SQL (Base de datos PostgreSQL)](03_cloud_sql.es.md)
- 04 — Secret Manager (Capítulo actual)
- [05 — Cloud Storage (Media & static files)](05_cloud_storage.es.md)
- [06 — Dockerfile](06_dockerfile.es.md)
- [07 — Primer Despliegue](07_first_deploy.es.md)
- [08 — Dominio Personalizado y SSL](08_domain_ssl.es.md)
- [09 — Workload Identity Federation (Auth de GitHub sin llaves)](09_workload_identity.es.md)
- [10 — Pipeline CI/CD con GitHub Actions](10_github_actions.es.md)
- [11 — Referencia Rápida](11_quick_reference.es.md)
- [12 — Bonus: Email Personalizado (@dominio.cl)](12_custom_email.es.md)
- [13 — Bonus: Django Tasks (Overview)](13_django_tasks.es.md)
  - [13.A — Cloud Tasks via HTTP](13_django_tasks_cloud_tasks.es.md)
  - [13.B — db_worker embebido](13_django_tasks_embedded.es.md)
