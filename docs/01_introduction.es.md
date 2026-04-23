---
description: "Conoce qué vamos a construir y por qué — una aplicación Django lista para producción en la nube con despliegue automatizado."
image: assets/social-banner.png
---

# 01 — Introducción: Qué vamos a construir

Esta guía te enseña cómo desplegar una aplicación web Django en la nube. Al terminar, tendrás un pipeline automatizado donde cada push a GitHub construye, prueba y despliega automáticamente tu aplicación.

---

## Qué vamos a construir

Una aplicación web Django lista para producción ejecutándose en Google Cloud Platform (GCP), usando:

- **Terraform** para gestionar toda la infraestructura como código
- **Cloud Run** para ejecutar tu contenedor Docker (sin servidor, escala a cero)
- **PlanetScale** para la base de datos Postgres gestionada
- **Cloud Tasks** para procesamiento de trabajos en segundo plano
- **GitHub Actions** para CI/CD automatizado

---

## El problema que resolvemos

Antes de esta guía:
1. Haces clic en una consola de nube para crear recursos
2. Ejecutas comandos CLI para desplegar
3. Esperas que nada se rompa y que recuerdes todos los pasos

Después de esta guía:
1. Escribes archivos de Terraform describiendo lo que quieres
2. Haces push a GitHub
3. Todo sucede automáticamente

---

## Para quién es esta guía

- Desarrolladores Django que quieren desplegar a producción
- Desarrolladores nuevos en infraestructura en la nube (GCP, AWS, etc.)
- Cualquiera cansado de procesos de despliegue manuales y propensos a errores

No se requiere experiencia previa con nube o Terraform.

---

## Lo que aprenderás

- Cómo funciona Terraform y por qué es mejor que los comandos manuales
- Cómo cada servicio en la nube encaja en la arquitectura general
- Cómo configurar una infraestructura completa usando Terraform
- Cómo contenerizar una aplicación Django con Docker
- Cómo automatizar el despliegue con GitHub Actions
- Cómo conectar un dominio personalizado con SSL gratis

---

## El panorama general

```
Push a GitHub
    │
    └── GitHub Actions
              │
              ├── Ejecutar tests
              ├── Construir imagen Docker
              ├── Subir a Artifact Registry
              │
              ▼
         Cloud Run (web)
              │
              ├── Lee secretos de Secret Manager
              ├── Lee/escribe a Cloud Storage
              ├── Se conecta a PlanetScale (Postgres)
              └── Envía trabajo a Cloud Tasks
                        │
                        ▼
              Cola de Cloud Tasks + worker
```

---

## Servicios explicados

### Plataforma de contenedores — Cloud Run

Tu aplicación Django se ejecuta como un **contenedor Docker** en Cloud Run. Es sin servidor — escala a cero cuando está inactiva, escala automáticamente bajo carga, maneja HTTPS automáticamente.

En esta guía: **Cloud Run** (GCP)

### Trabajos en segundo plano — Cloud Tasks

Algunas tareas son muy lentas para ejecutar dentro de una solicitud web (envío de emails, generación de PDFs). Cloud Tasks te permite encolar estos trabajos y procesarlos en segundo plano.

En esta guía: **Cloud Tasks** (GCP)

### Tareas programadas — Cloud Scheduler

Cloud Scheduler activa trabajos en segundo plano en un horario tipo cron (ej., "verificar cada minuto si hay tareas pendientes").

En esta guía: **Cloud Scheduler** (GCP)

### Almacenamiento de objetos — Cloud Storage

Los archivos estáticos (CSS, JS) y las subidas de usuarios van aquí, no en el sistema de archivos del contenedor.

En esta guía: **Cloud Storage** (GCP)

### Registro de contenedores — Artifact Registry

Las imágenes Docker se almacenan aquí, no en Docker Hub. Privado, dentro de tu proyecto en la nube.

En esta guía: **Artifact Registry** (GCP)

### Gestión de secretos — Secret Manager

Contraseñas, claves API, cadenas de conexión — almacenadas de forma segura, inyectadas en tiempo de ejecución.

En esta guía: **Secret Manager** (GCP)

### Postgres gestionado — Base de datos

Una base de datos completamente gestionada — sin mantenimiento de servidor, los respaldos se manejan automáticamente, y escala sin servidor. La conexión es una cadena de conexión Postgres estándar.

En esta guía: **PlanetScale** (Postgres sin servidor con flujo de trabajo de ramificación)

### GitHub Actions — CI/CD

GitHub Actions ejecuta tu pipeline en cada push:
1. Ejecutar tests
2. Construir imagen Docker
3. Subir a registro de contenedores
4. Ejecutar cualquier trabajo de migración o configuración
5. Desplegar la nueva versión

### Workload Identity — Autenticación segura

Workload Identity permite a GitHub Actions autenticarse en GCP sin almacenar claves JSON — más seguro, sin necesidad de rotación manual.

En esta guía: **Workload Identity Federation** (GCP)

---

## Navegación



- 01 — Introduction: What We're Building (Capítulo actual)
- [02 — Terraform Overview](02_terraform_overview.es.md)
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