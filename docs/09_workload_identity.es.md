---
description: "Configura Workload Identity Federation sin claves para que GitHub Actions se autentique en GCP de forma segura sin usar claves JSON."
image: assets/social-banner.png

---
# 09 — Workload Identity Federation (Autenticación sin claves en GitHub Actions)

← [Anterior: 08 — Dominio Personalizado y SSL](08_domain_ssl.md)

> ✅ **Gratuito.** Workload Identity Federation no tiene costo.

## El problema con las claves de service account

La forma naive de autenticar GitHub Actions en GCP es crear un archivo de clave JSON para la service account y pegarlo en un secret de GitHub. Esto funciona pero tiene riesgos: el archivo de clave nunca expira, si se filtra da acceso total hasta que se revoque manualmente, y rotarlo requiere pasos manuales.

## ¿Qué es Workload Identity Federation?

Workload Identity Federation permite que GitHub Actions pruebe su identidad ante GCP usando un token OIDC de corta duración (como un carnet de identidad temporal) en lugar de una clave permanente. El flujo es:

![Mapa conceptual de Workload Identity](assets/diagram-wif.svg)

1. GitHub Actions solicita un JWT firmado del proveedor OIDC de GitHub, afirmando "Soy un workflow ejecutándose en el repo `TU_ORG/TU_REPO` en la rama `main`"
2. El Workload Identity Pool de GCP verifica la firma del JWT contra las claves públicas de GitHub
3. GCP emite un token de acceso de GCP de corta duración (válido por ~1 hora)
4. El workflow usa ese token para subir imágenes y desplegar

Nunca se almacenan credenciales permanentes en ningún lugar.

---

## Configuración (una vez, ejecuta en tu terminal local)

```bash
# Obtiene el ID numérico del proyecto — necesario para construir el nombre del recurso de Workload Identity.
PROJECT_NUMBER=$(gcloud projects describe mycoolproject-prod --format='value(projectNumber)')

# Crea un Workload Identity Pool — un contenedor para proveedores de identidad externos.
# Piénsalo como un límite de confianza: solo los proveedores dentro de este pool pueden intercambiar tokens.
# Resultado: visible en console.cloud.google.com/iam-admin/workload-identity-pools
gcloud iam workload-identity-pools create github-pool \
  --location=global \
  --display-name="GitHub Actions Pool"

# Crea un proveedor OIDC dentro del pool que confíe en los tokens JWT de GitHub Actions.
# attribute.repository mapea el claim de repo del JWT para poder restringir a repos específicos.
# Le dice a GCP: "acepta tokens de corta duración firmados por el emisor OIDC de GitHub".
gcloud iam workload-identity-pools providers create-oidc github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --display-name="GitHub provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"
```

Explicación del mapeo de atributos:

- `google.subject=assertion.sub` — mapea el campo `sub` del JWT al sujeto de GCP
- `attribute.repository=assertion.repository` — expone el nombre del repo como atributo de GCP para poder restringir a repos específicos

```bash
# Otorga a los workflows de TU_ORG/TU_REPO permiso para suplantar a mycoolproject-run-sa.
# Este es el límite de seguridad clave: solo tu repo puede convertirse en esa service account.
# Reemplaza TU_ORG/TU_REPO con tu org y nombre de repo actuales de GitHub (por ejemplo, acme/mycoolproject).
gcloud iam service-accounts add-iam-policy-binding \
  mycoolproject-run-sa@mycoolproject-prod.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/attribute.repository/TU_ORG/TU_REPO"
```

Este binding dice: "los workflows que se ejecutan desde `TU_ORG/TU_REPO` pueden actuar como `mycoolproject-run-sa`". Los workflows de cualquier otro repo no pueden.

```bash
# Imprime el nombre completo del recurso del proveedor — copia este valor en el
# secret de GitHub GCP_WORKLOAD_IDENTITY_PROVIDER en el siguiente paso.
gcloud iam workload-identity-pools providers describe github-provider \
  --location=global \
  --workload-identity-pool=github-pool \
  --format="value(name)"
```

La salida se ve así:
```
projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider
```

---

## Agregar Secrets de GitHub

Ve a **GitHub → tu repo → Settings → Secrets and variables → Actions → New repository secret**:

| Nombre del secret | Valor |
|---|---|
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | El nombre completo del recurso del proveedor del último comando |
| `GCP_SERVICE_ACCOUNT` | `mycoolproject-run-sa@mycoolproject-prod.iam.gserviceaccount.com` |

Estos son los únicos dos valores que GitHub necesita. Sin archivo de clave JSON, sin contraseña.

---

## Cómo los usa el workflow

En el workflow de GitHub Actions (capítulo 10), este paso intercambia el token OIDC de GitHub por un token de acceso de GCP:

```yaml
- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: ${{ secrets.GCP_WORKLOAD_IDENTITY_PROVIDER }}
    service_account: ${{ secrets.GCP_SERVICE_ACCOUNT }}
```

Después de este paso, los comandos `gcloud` y `docker` en el workflow usan automáticamente las credenciales de GCP. El token expira cuando termina el workflow.

---

## 📖 Navegación

- [01 — Configuración del Proyecto GCP](01_gcp_setup.md)
- [02 — Artifact Registry](02_artifact_registry.md)
- [03 — Cloud SQL (Base de Datos PostgreSQL)](03_cloud_sql.md)
- [04 — Secret Manager](04_secret_manager.md)
- [05 — Cloud Storage (Archivos media y static)](05_cloud_storage.md)
- [06 — Dockerfile](06_dockerfile.md)
- [07 — Primer Despliegue](07_first_deploy.md)
- [08 — Dominio Personalizado y SSL](08_domain_ssl.md)
- **09 — Workload Identity Federation (Autenticación sin claves en GitHub Actions)** (capítulo actual)
- [10 — Pipeline CI/CD con GitHub Actions](10_github_actions.md)
- [11 — Referencia Rápida](11_quick_reference.md)
