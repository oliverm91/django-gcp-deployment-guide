---
description: "Crea y conecta de forma segura una base de datos PostgreSQL gestionada con Cloud SQL para tu aplicación Django en producción."
image: assets/social-banner.png

---
# 03 — Cloud SQL (Base de Datos PostgreSQL)

← [Anterior: 02 — Artifact Registry](02_artifact_registry.md)

> 💰 **Cuesta dinero — configúralo de último, justo antes de salir a producción.**
>
> Cloud SQL **no tiene nivel gratuito**. La instancia más pequeña (`db-f1-micro`) cuesta aproximadamente **$7–10/mes** y el cobro comienza en el momento en que la creas, sin importar si la app está activa o no. Pausar la instancia detiene el cobro de cómputo, pero sigue cobrando por almacenamiento.
>
> **Recomendado:** completa todos los demás capítulos primero. Crea la instancia de Cloud SQL solo cuando estés listo para desplegar y salir a producción, para minimizar el gasto en inactividad.

## ¿Qué es Cloud SQL?

Cloud SQL es el servicio de PostgreSQL gestionado de Google. "Gestionado" significa que Google se encarga del servidor, los parches del sistema operativo, los backups y la alta disponibilidad — tú simplemente te conectas y lo usas como una base de datos PostgreSQL normal. Nunca necesitas acceder al servidor de base de datos por SSH.

## ¿Cómo se conecta Cloud Run a Cloud SQL?

Cloud Run se conecta a Cloud SQL a través de un **socket Unix** — no por internet, no por una IP pública. El Cloud SQL Auth Proxy se ejecuta como un sidecar dentro de Cloud Run y expone la base de datos en `/cloudsql/<instance-connection-name>`. La cadena de conexión usa esta ruta del socket:

```
postgresql://user:password@/dbname?host=/cloudsql/mycoolproject-prod:southamerica-east1:mycoolproject-db
```

Esto significa que la base de datos nunca es accesible públicamente — sin reglas de firewall, sin configuración de VPC necesaria.

---

## Crear la instancia

Ejecuta en tu **terminal local**:

```bash
# Crea una instancia gestionada de PostgreSQL 15. Tarda entre 3 y 5 minutos.
# ⚠️  La facturación comienza inmediatamente después de la creación (~$7/mes). Ejecuta esto solo cuando estés listo para salir a producción.
# Resultado: visible en console.cloud.google.com/sql/instances
gcloud sql instances create mycoolproject-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=southamerica-east1 \
  --storage-auto-increase \
  --backup-start-time=03:00 \
  --retained-backups-count=7
```

Opciones explicadas:

- `--tier=db-f1-micro` — instancia más pequeña, 0.6 GB de RAM (~$7/mes). Suficiente para tráfico inicial.
- `--storage-auto-increase` — el disco crece automáticamente a medida que crecen los datos.
- `--backup-start-time=03:00` — backup automático diario a las 3 AM UTC.
- `--retained-backups-count=7` — conserva 7 días de backups para recuperación a un punto en el tiempo.

Esto tarda entre 3 y 5 minutos en aprovisionarse.

---

## Crear la base de datos y el usuario

```bash
# Crea una base de datos llamada "mycoolproject" dentro de la instancia.
# La instancia es el servidor; la base de datos es un espacio de nombres lógico dentro de él.
# Resultado: visible en console.cloud.google.com/sql/instances/mycoolproject-db/databases
gcloud sql databases create mycoolproject --instance=mycoolproject-db

# Crea un usuario PostgreSQL dedicado para la app Django.
# Nunca uses el superusuario postgres predeterminado en producción — tiene acceso irrestricto.
# Genera una contraseña fuerte con: openssl rand -base64 32
# Guardarás esta contraseña en Secret Manager (capítulo 04) — no necesitas memorizarla.
gcloud sql users create djangouser \
  --instance=mycoolproject-db \
  --password=<contraseña-fuerte>
```

Usa una contraseña aleatoria fuerte aquí (por ejemplo, `openssl rand -base64 32`). La guardarás en Secret Manager en el capítulo siguiente — no necesitas recordarla.

---

## La cadena de conexión

El secret `DATABASE_URL` que crearás en Secret Manager usa este formato:

```
postgresql://djangouser:<contraseña>@/mycoolproject?host=/cloudsql/mycoolproject-prod:southamerica-east1:mycoolproject-db
```

Desglose:

- `djangouser` — el usuario de BD creado arriba
- `<contraseña>` — la contraseña establecida arriba
- `/mycoolproject` — el nombre de la base de datos
- `host=/cloudsql/...` — la ruta del socket Unix a Cloud SQL (sin IP pública)

Django lee esto a través de `DATABASE_URL` en `prod.py`:

```python
# web/core/settings/base.py
DATABASES = {
    'default': env.db('DATABASE_URL', default='...')
}
```

`env.db()` analiza la URL y construye el diccionario `DATABASES` de Django automáticamente usando `django-environ`.

---

## Migraciones

Las migraciones son la forma en que Django mantiene el esquema de la base de datos sincronizado con tus modelos. Cada vez que agregas un campo o creas un modelo, Django genera un archivo de migración. Estos deben aplicarse a la base de datos antes de que el nuevo código se ejecute.

En esta configuración, las migraciones se ejecutan como un **Cloud Run Job** — una ejecución de contenedor única que ejecuta `manage.py migrate` contra la base de datos de producción antes de cada despliegue. Consulta el [capítulo 07](07_first_deploy.md) para la configuración.

---

## 📖 Navegación

- [01 — Configuración del Proyecto GCP](01_gcp_setup.md)
- [02 — Artifact Registry](02_artifact_registry.md)
- **03 — Cloud SQL (Base de Datos PostgreSQL)** (capítulo actual)
- [04 — Secret Manager](04_secret_manager.md)
- [05 — Cloud Storage (Archivos media y static)](05_cloud_storage.md)
- [06 — Dockerfile](06_dockerfile.md)
- [07 — Primer Despliegue](07_first_deploy.md)
- [08 — Dominio Personalizado y SSL](08_domain_ssl.md)
- [09 — Workload Identity Federation (Autenticación sin claves en GitHub Actions)](09_workload_identity.md)
- [10 — Pipeline CI/CD con GitHub Actions](10_github_actions.md)
- [11 — Referencia Rápida](11_quick_reference.md)
