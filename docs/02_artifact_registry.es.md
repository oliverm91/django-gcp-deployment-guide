---
description: "Crea un registro privado de imágenes Docker en GCP con Artifact Registry para almacenar de forma segura las imágenes de tu app Django."
image: assets/social-banner.png

---
# 02 — Artifact Registry

← [Anterior: 01 — Configuración del Proyecto GCP](01_gcp_setup.md)

> ✅ **Prácticamente gratuito.** Los primeros 0.5 GB de almacenamiento por mes son gratuitos. Una imagen Django típica ocupa ~200–300 MB, por lo que al inicio te mantendrás dentro del nivel gratuito. Después de eso, el almacenamiento cuesta $0.10/GB/mes. El tráfico de red entre Artifact Registry y Cloud Run en la misma región es gratuito.

## ¿Qué es Artifact Registry?

Artifact Registry es el registro privado de imágenes de contenedores de GCP — el lugar donde se almacenan las imágenes Docker antes de ser desplegadas. Piénsalo como Docker Hub, pero privado y dentro de tu proyecto GCP.

Cuando [GitHub Actions construye una imagen Docker con tu código](10_github_actions.md), la sube aquí. Cuando Cloud Run despliega, descarga la imagen desde aquí. La imagen nunca sale de la red de GCP.

## ¿Qué es una imagen Docker?

Una imagen Docker es un snapshot empaquetado y autónomo de tu aplicación: el runtime de Python, todas las dependencias, tu código Django y el comando para iniciar el servidor — todo agrupado en un solo archivo. Cloud Run toma esta imagen y la ejecuta como un contenedor (un proceso activo).

---

## Crear el repositorio

```bash
# Crea un registro privado de imágenes Docker dentro de tu proyecto GCP.
# Aquí es donde GitHub Actions subirá las imágenes construidas y Cloud Run las descargará.
# Resultado: visible en console.cloud.google.com/artifacts — la URL del registro será
# southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/
gcloud artifacts repositories create mycoolproject-repo \
  --repository-format=docker \
  --location=southamerica-east1
```

Esto crea un repositorio en:
```
southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/
```

Las imágenes subidas aquí se llamarán:
```
southamerica-east1-docker.pkg.dev/mycoolproject-prod/mycoolproject-repo/app:<tag>
```

Tags usados en esta guía:

- `latest` — siempre apunta a la compilación más reciente
- `<git-sha>` — por ejemplo `a3f9c12` — tag único por commit, usado para rollbacks precisos

## Autenticar Docker para subir imágenes

Antes de subir imágenes desde tu máquina local (solo para el primer despliegue — GitHub Actions lo maneja automáticamente después):

```bash
# Configura Docker en tu máquina local para usar credenciales de gcloud al subir
# a este registro. Ejecutar una vez por máquina — no se necesita en GitHub Actions
# (lo maneja el workflow). Escribe un helper de credenciales en ~/.docker/config.json.
gcloud auth configure-docker southamerica-east1-docker.pkg.dev
```

Esto actualiza tu configuración local de Docker para que sepa usar credenciales de `gcloud` al subir imágenes a este registro.

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
