---
description: "Una guía completa para desplegar una aplicación web Django usando Terraform, cubriendo infraestructura en la nube, despliegue contenedorizado y CI/CD automatizado."
image: assets/social-banner.png
---

# Guía de Despliegue Django — Edición Terraform

¡Bienvenido! Esta guía te enseña cómo desplegar una aplicación web Django en la nube usando **Terraform** para gestionar toda la infraestructura como código.

Al terminar, tendrás un pipeline automatizado donde cada push a GitHub construye, prueba y despliega automáticamente tu aplicación — sin pasos manuales.

## Infraestructura como código

Toda la infraestructura en la nube de esta guía está definida en archivos de configuración de **Terraform**. En lugar de hacer clic en una consola web o ejecutar comandos CLI manuales, todo vive en archivos bajo control de versiones.

Beneficios de este enfoque:

- **Documentado** — toda tu infraestructura está en control de versiones
- **Reproducible** — destruir y recrear desde cero de forma confiable
- **Revisable** — los cambios son visibles en pull requests antes de aplicar
- **Portable** — el mismo lenguaje de configuración funciona en diferentes proveedores de nube

El flujo es: escribir configuración → ejecutar `terraform plan` para previsualizar → ejecutar `terraform apply` para crear.

## Qué construiremos

Esta guía implementa infraestructura en **Google Cloud Platform (GCP)** con una base de datos Postgres de **PlanetScale**.

Tu aplicación se ejecuta como un **contenedor Docker** en una plataforma de contenedores sin servidor. Escala a cero cuando está inactiva (sin costo), escala automáticamente bajo carga y maneja HTTPS automáticamente.

La infraestructura consiste en:

- **Plataforma de contenedores** — ejecuta tu Django como contenedor Docker
- **Cola de trabajos en segundo plano** — maneja trabajo asíncrono (envío de emails, procesamiento de datos)
- **Tareas programadas** — activa trabajos en segundo plano en un horario tipo cron
- **Almacenamiento de objetos** — archivos estáticos (CSS, JS) y medios subidos por usuarios
- **Registro de contenedores** — almacenamiento privado para imágenes Docker
- **Gestión de secretos** — credenciales almacenadas de forma segura, inyectadas en tiempo de ejecución
- **Postgres gestionado** — base de datos sin servidor con flujo de trabajo de ramificación
- **GitHub Actions** — pipeline CI/CD para despliegues automatizados
- **Workload Identity** — autenticación segura sin claves de GitHub a tu nube

## Arquitectura

```
Push a GitHub
    │
    └── GitHub Actions (CI/CD)
              │
              ├── Ejecutar tests
              ├── Construir imagen Docker
              ├── Subir a Registro de Contenedores
              │
              ▼
         Plataforma de Contenedores (web)
              │
              ├── Lee secretos de Secret Manager
              ├── Lee/escribe archivos a Object Storage
              ├── Se conecta a Postgres gestionado
              └── Envía trabajo en segundo plano a Job Queue
                        │
                        ▼
                   Cola de Trabajos en Segundo Plano
                        │
                        ▼
                   Worker de Jobs (contenedor separado)
```

## Capítulos

La guía está estructurada en tres partes:

### Parte 1 — Fundamentos (sin código todavía)

1. [Introducción — Qué construiremos](01_introduction.es.md)
2. [Visión general de Terraform](02_terraform_overview.es.md)
3. [Servicios en la nube explicados](03_cloud_services.es.md)
4. [Postgres gestionado explicado](04_planetscale.es.md)

### Parte 2 — Infraestructura con Terraform

5. [Configuración del proyecto y estado de Terraform](05_project_setup.es.md)
6. [Proyecto GCP y APIs](06_gcp_project.es.md)
7. [Artifact Registry](07_artifact_registry.es.md)
8. [Gestión de Secretos](09_secrets.es.md)
9. [Object Storage](10_storage.es.md)
10. [Service Accounts e IAM](11_iam.es.md)
11. [Cloud Run](12_cloud_run.es.md)
12. [Trabajos en segundo plano y Scheduler](13_tasks.es.md)

### Parte 3 — Despliegue y Automatización

13. [Dockerfile](14_dockerfile.es.md)
14. [Primer Despliegue](15_first_deploy.es.md)
15. [Dominio personalizado y SSL](16_domain_ssl.es.md)
16. [Workload Identity Federation](17_wif.es.md)
17. [GitHub Actions CI/CD](18_github_actions.es.md)
18. [Referencia Rápida](19_quick_reference.es.md)

---

## Requisitos previos

- Un repositorio GitHub con tu proyecto Django
- Una cuenta en la nube (GCP en esta guía — cuentas nuevas reciben $300 en créditos gratuitos)
- Una cuenta de Postgres gestionado (PlanetScale en esta guía — planes de pago desde $5/mes)
- CLI `gcloud` instalado y autenticado (para GCP)
- Docker instalado localmente
- Terraform instalado

---

## Resumen de costos

Esta guía usa GCP y PlanetScale. Los costos abajo reflejan esos servicios:

| Servicio | Nivel gratuito | Costo después del nivel gratuito |
|---|---|---|
| Plataforma de contenedores | 2M solicitudes + 360K CPU GB-s/mes | ~$0.00004/solicitud |
| Registro de contenedores | 0.5 GB/mes | $0.10/GB/mes |
| Gestión de secretos | 6 secretos + 10K accesos/mes | $0.06/secreto/mes |
| Object storage | 5 GB/mes | ~$0.023/GB/mes |
| Trabajos en segundo plano | Gratis hasta 1M acciones/mes | $0.40/millón |
| Programador de tareas | 3 trabajos gratis/mes | $0.10/trabajo/mes |
| GitHub Actions | 2,000 min/mes (repo privado) | $0.008/min |
| Workload Identity | Ilimitado | Gratis |
| Postgres gestionado | Sin plan gratuito | **$5/mes** para Postgres de un solo nodo |
| Certificado SSL | Gratis (gestionado) | — |

> **PlanetScale** no tiene plan gratuito. Todas las bases de datos requieren una suscripción de pago. Postgres de un solo nodo comienza en **$5/mes**.

### Estimación de costo para bajo tráfico

Para un proyecto hobby o sitio de bajo tráfico con escala-a-cero habilitada:

| Servicio | Costo mensual |
|---|---|
| Plataforma de contenedores | $0 (dentro del nivel gratuito) |
| Registro de contenedores | $0 (dentro del nivel gratuito) |
| Gestión de secretos | $0 (dentro del nivel gratuito) |
| Object storage | ~$1 (5 GB estático + 1 GB medios) |
| Trabajos en segundo plano | $0 (dentro del nivel gratuito) |
| Programador de tareas | $0.30 (3 trabajos, primeros 3 gratis) |
| GitHub Actions | $0 (dentro del nivel gratuito) |
| Postgres gestionado | **$5** |
| **Total** | **~$6–7/mes** |

La escala-a-cero de Cloud Run significa que no pagas nada cuando no hay tráfico. Los costos de arriba aplican a un sitio con ligera actividad de trabajos en segundo plano.

## Introducción al proyecto
[Introducción — Qué construiremos](01_introduction.es.md)
