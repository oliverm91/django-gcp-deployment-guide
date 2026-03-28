import glob
import os

titles_es = {
    "01_gcp_setup.md": "01 — Configuración del Proyecto GCP",
    "02_artifact_registry.md": "02 — Artifact Registry",
    "03_cloud_sql.md": "03 — Cloud SQL (Base de Datos PostgreSQL)",
    "04_secret_manager.md": "04 — Secret Manager",
    "05_cloud_storage.md": "05 — Cloud Storage (Archivos Estáticos y Multimedia)",
    "06_dockerfile.md": "06 — Dockerfile",
    "07_first_deploy.md": "07 — Primer Despliegue",
    "08_domain_ssl.md": "08 — Dominio Personalizado y SSL",
    "09_workload_identity.md": "09 — Workload Identity Federation (Autenticación sin Claves)",
    "10_github_actions.md": "10 — Pipeline CI/CD con GitHub Actions",
    "11_quick_reference.md": "11 — Referencia Rápida",
    "index.md": "Guía de Despliegue de Django en GCP"
}

index_español = """---
description: "Una guía completa para implementar una aplicación web Django en Google Cloud Platform usando Cloud Run, Cloud SQL y GitHub Actions."
image: assets/social-banner.png
---
# Guía de despliegue de Django en GCP

¡Bienvenido! Esta guía centrada en la práctica te enseñará exactamente cómo tomar un proyecto local de Django y desplegarlo profesionalmente en Google Cloud Platform utilizando patrones de infraestructura modernos y altamente escalables.

Al final de estos capítulos, habrás construido una canalización CI/CD completamente automatizada desde cero. Cada vez que subas código nuevo a GitHub, tu aplicación se compilará, se probará automáticamente y se publicará en internet al instante, sin intervención manual.

---

## Qué se despliega

Aunque usamos una aplicación web genérica de Django como base, **los conceptos principales que aprenderás aquí se aplican a casi cualquier framework web moderno**. 

Tu aplicación final se ejecutará como un **contenedor Docker** protegido y alojado en **Cloud Run**, el potente motor serverless de Google. Esto significa que tu aplicación escalará sin esfuerzo para manejar picos de tráfico enormes y bajará su escala hasta cero cuando esté inactiva para ahorrarte dinero.

## Arquitectura

![Arquitectura](assets/diagram-runtime.svg)

**El flujo automatizado:** Cuando fusionas una nueva característica en la rama `main`, GitHub Actions se activa automáticamente. Utiliza Workload Identity para iniciar sesión en tu cuenta de forma segura. Limpiamente empaqueta tu código en una nueva imagen Docker y le indica a Cloud Run que despliegue la nueva versión en segundos.

## Capítulos

1. [Configuración del Proyecto GCP](01_gcp_setup.md)
2. [Artifact Registry](02_artifact_registry.md)
3. [Cloud SQL — Base de datos](03_cloud_sql.md)
4. [Secret Manager](04_secret_manager.md)
5. [Cloud Storage](05_cloud_storage.md)
6. [Dockerfile](06_dockerfile.md)
7. [Primer Despliegue](07_first_deploy.md)
8. [Dominio Personalizado](08_domain_ssl.md)
9. [Workload Identity](09_workload_identity.md)
10. [GitHub Actions (CI/CD)](10_github_actions.md)
11. [Referencia Rápida](11_quick_reference.md)
"""

for path in glob.glob("docs/*.md"):
    if path.endswith(".es.md"):
        continue

    basename = os.path.basename(path)
    new_path = path.replace(".md", ".es.md")

    if basename == "index.md":
        with open(new_path, "w", encoding="utf-8") as f:
            f.write(index_español)
        continue

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Base naive translations for structural english words to spanish
    content = content.replace("← [Previous:", "← [Anterior:")
    content = content.replace("Next:", "Siguiente:")
    content = content.replace("current chapter", "capítulo actual")
    content = content.replace("This chapter", "Este capítulo")
    content = content.replace("Navigation", "Navegación")
    
    # Update internal nav links inside the es.md pointing to other chapters to automatically resolve
    # Note: mkdocs static i18n seamlessly resolves original link names like 01_gcp_setup.md directly to the .es.md output HTML if available!
    
    with open(new_path, "w", encoding="utf-8") as f:
        f.write(content)
