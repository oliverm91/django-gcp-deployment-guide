---
description: "Configura buckets de Cloud Storage para manejar archivos static y media subidos por usuarios mediante django-storages."
image: assets/social-banner.png

---
# 05 — Cloud Storage (Archivos media y static)

← [Anterior: 04 — Secret Manager](04_secret_manager.md)

> ✅ **Prácticamente gratuito al inicio.** Los primeros 5 GB/mes de almacenamiento regional son gratuitos. Los archivos static (CSS, JS, íconos) suman ~2–3 MB en total. Los archivos media crecen con las subidas de los usuarios — un marketplace con algunos cientos de publicaciones se mantiene bien dentro del nivel gratuito. Después de 5 GB, el almacenamiento cuesta ~$0.023/GB/mes y el egreso (servir archivos a los usuarios) cuesta ~$0.08/GB/mes.

## ¿Qué es Cloud Storage?

Cloud Storage (GCS) es el servicio de almacenamiento de objetos de Google — similar a Amazon S3. Los archivos se almacenan como objetos en buckets (espacios de nombres planos, no directorios). Es duradero (99.999999999% de durabilidad), accesible globalmente y económico.

## ¿Por qué no almacenar archivos en el contenedor?

Los contenedores de Cloud Run son **efímeros** — arrancan y se detienen bajo demanda, y múltiples instancias pueden ejecutarse simultáneamente. Cualquier archivo escrito en el sistema de archivos local del contenedor se pierde cuando este se detiene. Los archivos media (imágenes subidas por usuarios) y los archivos static (CSS, JS, íconos) deben vivir fuera del contenedor.

## Dos buckets

| Bucket | Contenido | Acceso |
|---|---|---|
| `mycoolproject-static` | CSS, JS, íconos, imágenes OG — generados por `collectstatic` | Público (cualquiera puede leer) |
| `mycoolproject-media` | Imágenes de publicaciones subidas por usuarios, avatares | Público (servido directamente via URL) |

---

## Crear los buckets

Ejecuta en tu **terminal local**:

```bash
# Crea los dos buckets de GCS. Los nombres de buckets son únicos globalmente en todo GCP.
# -l establece la región — misma región que Cloud Run evita costos de egreso.
# Resultado: visible en console.cloud.google.com/storage/browser
gsutil mb -l southamerica-east1 gs://mycoolproject-media
gsutil mb -l southamerica-east1 gs://mycoolproject-static

# Otorga acceso de lectura público a los archivos static (CSS, JS, íconos).
# Sin esto, los navegadores recibirían un 403 al cargar las hojas de estilo del sitio.
gsutil iam ch allUsers:objectViewer gs://mycoolproject-static

# Otorga acceso de lectura público a los archivos media (imágenes de publicaciones, avatares subidos por usuarios).
# Sin esto, las imágenes subidas no se mostrarían en las publicaciones.
gsutil iam ch allUsers:objectViewer gs://mycoolproject-media
```

> `gsutil` es parte del CLI de `gcloud`.

---

## Configurar Django para usar GCS

### Instalar django-storages

`django-storages` es una librería de Django que reemplaza el backend de almacenamiento de archivos predeterminado con proveedores en la nube (GCS, S3, Azure, etc.).

```bash
# Agrega django-storages con el backend de Google Cloud Storage.
# [google] instala la dependencia google-cloud-storage necesaria para comunicarse con GCS.
# Esto actualiza pyproject.toml y uv.lock — haz commit de ambos archivos después de ejecutar.
cd web
uv add django-storages[google]
```

Esto agrega `django-storages` y `google-cloud-storage` a `pyproject.toml`. El extra `[google]` instala las dependencias específicas de GCS.

### Configuración en `prod.py`

Lo siguiente va en `web/core/settings/prod.py`. Solo aplica en producción — el desarrollo local sigue usando el sistema de archivos local.

```python
# web/core/settings/prod.py

STORAGES = {
    # Almacenamiento predeterminado: adónde van las subidas de FileField/ImageField (media de usuarios)
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {"bucket_name": "mycoolproject-media"},
    },
    # Almacenamiento de archivos static: adónde pone collectstatic los archivos
    "staticfiles": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": "mycoolproject-static",
            "default_acl": None,
            "object_parameters": {"cache_control": "public, max-age=31536000"},
        },
    },
}

GS_PROJECT_ID = "mycoolproject-prod"
STATIC_URL = "https://storage.googleapis.com/mycoolproject-static/"
MEDIA_URL  = "https://storage.googleapis.com/mycoolproject-media/"
```

`cache_control: public, max-age=31536000` le indica a los navegadores que almacenen en caché los archivos static por 1 año — dado que `collectstatic` genera nombres de archivo con hash de contenido, los cachés obsoletos nunca son un problema.

### ¿Cómo escribe Django en GCS sin credenciales?

El contenedor de Cloud Run se ejecuta como `mycoolproject-run-sa` (la service account del capítulo 01), que tiene el rol `roles/storage.objectAdmin`. Las librerías cliente de Google recogen automáticamente la identidad de la service account desde el servidor de metadatos del contenedor — no se necesita ningún archivo de credenciales.

---

## Recolectar archivos static

### Archivos static vs archivos media

Los **archivos static** (CSS, JS, íconos) son parte de tu **código fuente** — son iguales para todos los usuarios y solo cambian cuando despliegas código nuevo. Deben subirse a GCS antes del primer despliegue para que los navegadores puedan cargar los estilos al visitar el sitio.

Los **archivos media** (imágenes subidas por usuarios, avatares) son creados en **tiempo de ejecución** por los usuarios. Son subidos directamente por la app cuando los usuarios envían formularios — no se requiere un paso separado de "recolección". Django los escribe en GCS automáticamente a través del backend de `storages`.

### Cómo funciona el comando

```bash
# Establece una variable de entorno solo para la ejecución de este comando, luego ejecuta collectstatic.
# DJANGO_SETTINGS_MODULE=core.settings.prod le dice a Django que cargue la configuración de prod.py,
# que configura el backend de GCS para que collectstatic sepa subir a gs://mycoolproject-static.
# --noinput omite las confirmaciones (útil para automatización).
# Resultado: Django reúne todo el CSS/JS/íconos, agrega hashes de contenido y sube a GCS
# (la subida ocurre automáticamente a través del backend de storages — no se necesita gcloud/gsutil).
cd web
DJANGO_SETTINGS_MODULE=core.settings.prod uv run manage.py collectstatic --noinput
```

**Qué sucede internamente:**

1. Django carga la configuración de `prod.py` (porque `DJANGO_SETTINGS_MODULE` apunta a ella)
2. Lee la configuración de `STORAGES["staticfiles"]`, que especifica el backend de GCS y el nombre del bucket
3. Escanea todos los directorios `static/` del proyecto
4. Procesa los archivos (minifica CSS/JS, agrega hashes de contenido a los nombres de archivo)
5. El backend de GCS de `django-storages` los sube automáticamente a `gs://mycoolproject-static/`
6. No se necesitan comandos explícitos de `gcloud` o `gsutil` — el backend lo maneja

Después de ejecutar esto, `https://storage.googleapis.com/mycoolproject-static/` sirve todo el CSS, JS e íconos.

### Cuándo ejecutar esto

Ejecútalo **antes del primer despliegue** y después de cualquier cambio en CSS/JS/íconos.

En despliegues posteriores, el pipeline de GitHub Actions puede ejecutar esto automáticamente — agrégalo como un paso antes del build de Docker si es necesario.

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
