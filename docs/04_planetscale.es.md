---
description: "Comprende qué es PlanetScale, cómo funciona su Postgres sin servidor, el flujo de trabajo de ramificación y cómo conectarse desde Django."
image: assets/social-banner.png
---

# 04 — Base de datos PlanetScale explicada

← [Anterior: 03 — Servicios en la nube explicados](03_cloud_services.es.md)

PlanetScale es la base de datos Postgres gestionada que usaremos en lugar de Cloud SQL de GCP. Este capítulo explica cómo funciona, por qué la elegimos y los conceptos clave que necesitas entender antes de configurarla.

---

## ¿Qué es PlanetScale?

PlanetScale es una **base de datos Postgres gestionada**. Es sin servidor, lo que significa:

- Sin gestión de servidores (sin parches, sin respaldos que gestionar, sin escalado que preocupar)
- Te conectas a una URL de base de datos — PlanetScale maneja todo lo demás
- Escala automáticamente para manejar picos de tráfico

### Comparado con Cloud SQL

| Característica | Cloud SQL | PlanetScale |
|---|---|---|
| Gestión de servidores | Tú lo gestionas | Completamente gestionado |
| Escalado | Manual (elegir tamaño de instancia) | Automático (sin servidor) |
| Ramificación | No | Sí (como ramas de Git) |
| Nivel gratuito | No | No (planes de pago desde $5/mes) |
| Costo | ~$7–10/mes (comienza inmediatamente) | $5/mes para Postgres de un solo nodo |

---

## Conceptos clave

### Base de datos vs Rama

En PlanetScale:

- **Base de datos** — la base de datos de producción donde viven tus datos
- **Rama** — una copia de la base de datos en la que puedes desarrollar, probar y fusionar de vuelta

Esto es como Git:
- Rama `main` = base de datos de producción
- Ramas de feature = ramas de desarrollo
- Fusionar = los cambios de esquema se aplican a producción

### Cambios de esquema como despliegues

El flujo de trabajo de ramificación de PlanetScale funciona muy bien con GitHub Actions:

1. Crea una rama para tu feature
2. Haz cambios de esquema (agregar columnas, etc.)
3. Abre un PR — PlanetScale puede ejecutar una "revisión de esquema" para mostrar qué cambiaría
4. Fusiona a main — PlanetScale aplica los cambios sin tiempo de inactividad

PlanetScale soporta **cambios de esquema no bloqueantes** — alterar tablas sin bloquearlas.

### Cadena de conexión

PlanetScale te da una cadena de conexión (como `postgres://user:password@aws.connect.psdb.cloud/db?sslmode=require`). Almacenas esto en Secret Manager y lo usas en el `DATABASE_URL` de Django.

---

## ¿Por qué PlanetScale para Django?

### Ventajas

1. **Sin servidor** — sin base de datos de servidor que gestionar
2. **Ramificación** — perfecto para probar migraciones antes de que lleguen a producción
3. **Sin mantenimiento** — sin respaldos que ejecutar, sin parches que aplicar
4. **Accesible** — Postgres de un solo nodo comienza en $5/mes
5. **Compatible con Django** — funciona con drivers Postgres estándar

### Desventajas

1. **Sin acceso superusuario** — no puedes hacer SSH o ejecutar `psql` directamente (es una conexión de solo lectura)
2. **Algunas características de Postgres limitadas** — no 100% de paridad con Postgres estándar (sin claves foráneas, algunos comportamientos de bloqueo difieren)
3. **Costo** — la base de datos de producción cuesta dinero

### Notas de compatibilidad para Django

PlanetScale es compatible con el ORM de Django, pero hay algunas advertencias:

1. **Sin restricciones de clave foránea** — PlanetScale no soporta claves foráneas debido a su naturaleza distribuida. Necesitarás usar `db_constraint=False` en campos ForeignKey o manejar la integridad referencial a nivel de aplicación.

2. **Sin `SELECT FOR UPDATE`** — algunas consultas de bloqueo no están soportadas.

3. **Migraciones** — las migraciones de Django funcionan bien, pero no puedes usar `migrate` para crear la base de datos inicial (PlanetScale la crea por ti vía su CLI).

Para la mayoría de las apps Django, estas limitaciones son manejables. Si necesitas características completas de Postgres, considera usar Cloud SQL en su lugar.

---

## CLI de PlanetScale

PlanetScale tiene una CLI (`pscale`) para gestionar bases de datos y ramas. La necesitarás para:

- Crear la base de datos inicial
- Crear ramas
- Ejecutar migraciones contra una rama
- Conectarte a una rama localmente

Instálala:

```bash
# macOS
brew install planetscale/tap/pscale

# Linux
curl -fsSL https://github.com/planetscale/cli/releases/download/v0.219.0/pscale_0.219.0_linux_amd64.tar.gz | tar -xz
sudo mv pscale /usr/local/bin/

# Verificar
pscale version
```

Autenticarse:

```bash
pscale auth login
```

---

## Creando la base de datos

### Vía el dashboard de PlanetScale

1. Ve a [app.planetscale.com](https://app.planetscale.com)
2. Crea una cuenta
3. Crea una nueva base de datos (llámala `mycoolproject`)
4. Anota la cadena de conexión

### Vía la CLI

```bash
pscale database create mycoolproject
```

---

## Ramas de base de datos

### Desarrollo vs Producción

- **Rama de desarrollo** — la rama predeterminada cuando creas una base de datos. Úsala para desarrollo local y pruebas de migraciones.

- **Rama de producción** — la base de datos de producción. Solo fusiona cambios de esquema aquí después de probar en la rama de desarrollo.

### Creando una rama

```bash
# Crear una rama para trabajar en un feature
pscale branch create mycoolproject feature-add-users

# Listar ramas
pscale branch list mycoolproject

# Eliminar una rama cuando termines
pscale branch delete mycoolproject feature-add-users
```

### Conectándose a una rama

Cada rama tiene su propia cadena de conexión. Usa la rama de desarrollo para desarrollo local, y solo conéctate a producción al desplegar.

```bash
# Obtener cadena de conexión para una rama (para desarrollo local)
pscale connect mycoolproject development
```

Esto abre un proxy local para que puedas conectarte a la rama de PlanetScale como si fuera una base de datos local.

---

## Conectándose desde Django

### El formato de la cadena de conexión

Las cadenas de conexión de PlanetScale se ven así:

```
postgres://user:password@aws.connect.psdb.cloud/db?sslmode=require
```

### Almacenar en Secret Manager

Almacena esto en Secret Manager usando la CLI de gcloud:

```bash
echo -n "postgres://user:password@aws.connect.psdb.cloud/mycoolproject?sslmode=require" \
  | gcloud secrets create DATABASE_URL --data-file=-
```

### Configuración de Django

Django lee esto vía `django-environ`:

```python
# web/core/settings/prod.py
import environ

env = environ.Env()

DATABASES = {
    'default': env.db('DATABASE_URL', default='sqlite:///db.sqlite3')
}
```

La variable de entorno `DATABASE_URL` se inyecta desde Secret Manager en tiempo de ejecución del contenedor. No se necesita configuración especial de PlanetScale — funciona con drivers Postgres estándar.

---

## Requisito de SSL/TLS

PlanetScale requiere conexiones SSL. El `?sslmode=require` en la cadena de conexión maneja esto. La mayoría de los drivers Postgres lo soportan de fábrica.

Si ves errores de SSL, verifica que tu cadena de conexión incluya `sslmode=require`.

---

## PlanetScale vs Cloud SQL

Aquí está la matriz de decisión:

| Escenario | Usar PlanetScale | Usar Cloud SQL |
|---|---|---|
| Empezando / aprendiendo | ✓ (planes de pago desde $5/mes) | ✗ (sin nivel gratuito) |
| App Django simple | ✓ | ✓ |
| Necesitas claves foráneas | ✗ | ✓ |
| Necesitas características completas de Postgres | ✗ | ✓ |
| Quieres flujo de trabajo de ramificación | ✓ | ✗ |
| Prefieres sin servidor | ✓ | ✗ |
| Presupuesto ajustado | ✗ (pago requerido) | ✓ (~$7/mes) |

Para esta guía, usamos PlanetScale por el flujo de trabajo de ramificación que combina bien con GitHub Actions, y el escalado sin servidor.

---

## Resumen: lo que hemos hecho

- Creamos una base de datos PlanetScale (vía dashboard o CLI)
- Almacenamos la cadena de conexión en Secret Manager
- Configuramos Django para leer `DATABASE_URL` desde el entorno

La infraestructura de Terraform (Artifact Registry, Cloud Run, IAM, otros secretos) se configura en los siguientes capítulos.

---

## Navegación



- [01 — Introduction: What We're Building](01_introduction.es.md)
- [02 — Terraform Overview](02_terraform_overview.es.md)
- [03 — Cloud Services Explained](03_cloud_services.es.md)
- 04 — PlanetScale Database Explained (Capítulo actual)
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