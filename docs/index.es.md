---
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
