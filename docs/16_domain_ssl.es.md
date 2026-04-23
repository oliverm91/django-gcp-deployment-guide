---
description: "Mapea tu dominio personalizado a Cloud Run y obtén un certificado SSL gratuito gestionado."
image: assets/social-banner.png
---

# 15 — Dominio personalizado y SSL

← [Anterior: 14 — Primer Despliegue](15_first_deploy.es.md)

Cloud Run te da una URL como `https://mycoolproject-abc123-uc.a.run.app` con HTTPS ya habilitado. Este capítulo muestra cómo usar tu propio dominio en su lugar.

---

## Cómo funciona SSL con Cloud Run

Cloud Run maneja SSL automáticamente vía certificados gestionados por Google. Solo apuntas tu dominio a Cloud Run y GCP aprovisiona y renueva el certificado gratis.

Dos opciones:

| Configuración | Quién gestiona SSL | Notas |
|---|---|---|
| Solo DNS de Cloudflare (nube gris) | GCP | Simple, gratis, certificado de Google |
| Cloudflare proxied (nube naranja) | Cloudflare | Añade protección WAF/DDoS, pero más complejo |

Esta guía usa DNS solo (nube gris) — configuración más simple.

---

## Mapear dominio a Cloud Run

```bash
# Mapear tu dominio al servicio Cloud Run
gcloud run domain-mappings create \
  --service=mycoolproject \
  --domain=mycoolproject.com \
  --region=southamerica-east1
```

Esto outputa un registro DNS para agregar. Algo como:
```
CNAME: mycoolproject.com → ghs.googlehosted.com
```

---

## Agregar registro DNS

Agrega el registro DNS en tu registrador o en Cloudflare.

### Configuración de Cloudflare

1. Agrega tu dominio a Cloudflare (plan gratuito)
2. Establece los nameservers en los de Cloudflare
3. Agrega el registro CNAME que Cloud Run te dio
4. Establece el modo proxy a **Solo DNS** (nube gris) ☁️

> **Importante:** Usa nube gris (Solo DNS), no naranja (proxied). La nube naranja hace que Cloudflare termine SSL, lo que rompe el aprovisionamiento de certificados de GCP y causa errores.

### Configuración de registrador directo

Agrega el registro CNAME o A que `gcloud run domain-mappings create` te indicó.

---

## Esperar el certificado SSL

El aprovisionamiento de SSL toma unos minutos hasta una hora después de que el DNS se propaga.

Verificar estado:

```bash
gcloud run domain-mappings describe \
  --domain=mycoolproject.com \
  --region=southamerica-east1
```

Busca `certificateMode: AUTOMATIC` y `mappingStatus: ACTIVE`.

---

## Actualizar ALLOWED_HOSTS

Una vez que el dominio esté activo, actualiza Cloud Run para aceptar solicitudes desde él:

```bash
gcloud run services update mycoolproject \
  --region=southamerica-east1 \
  --update-env-vars=ALLOWED_HOSTS="mycoolproject.com,www.mycoolproject.com,mycoolproject-abc123-uc.a.run.app"
```

El `ALLOWED_HOSTS` de Django rechaza solicitudes con `Host` headers desconocidos — esto previene ataques de HTTP Host header.

---

## Agregar subdominio www

Para manejar también `www.mycoolproject.com`:

```bash
gcloud run domain-mappings create \
  --service=mycoolproject \
  --domain=www.mycoolproject.com \
  --region=southamerica-east1
```

Agrega otro registro CNAME: `www.mycoolproject.com → mycoolproject.com` (o el mismo objetivo `ghs.googlehosted.com`).

---

## Configuración de Terraform para mapeo de dominio

Lamentablemente, los mapeos de dominio no pueden crearse con Terraform (GCP no los soporta aún en el provider de Google). Usa la CLI de `gcloud` o la Consola de GCP para este paso.

Pero puedes agregar el registro DNS vía Terraform si usas Cloudflare:

```hcl
# Cloudflare provider (separate from GCP)
provider "cloudflare" {
  api_token = var.cloudflare_api_token
}

resource "cloudflare_record" "www" {
  zone_id = var.cloudflare_zone_id
  name    = "www"
  value   = "ghs.googlehosted.com"
  type    = "CNAME"
  proxied = false  # Grey cloud — DNS only
}
```

---

## Notas de costo

| Elemento | Costo |
|---|---|
| Registro de dominio | ~$10–15/año (pagado al registrador, no a GCP) |
| Certificado SSL | Gratis (gestionado por GCP) |
| Cloudflare DNS | Gratis (en plan gratuito) |
| Cloudflare proxied | Gratis (pero rompe SSL de GCP — usa nube gris) |

---

## Verificar que el sitio funciona

```bash
curl https://mycoolproject.com/health/
```

Debería retornar `{"status": "ok"}`.

---

## Navegación



- [01 — Introducción: Qué vamos a construir](01_introduction.es.md)
- [02 — Visión general de Terraform](02_terraform_overview.es.md)
- [03 — Servicios en la nube explicados](03_cloud_services.es.md)
- [04 — Base de datos PlanetScale explicada](04_planetscale.es.md)
- [05 — Configuración del proyecto y estado de Terraform](05_project_setup.es.md)
- [06 — Proyecto GCP y APIs](06_gcp_project.es.md)
- [07 — Artifact Registry](07_artifact_registry.es.md)
- [08 — Gestión de Secretos](09_secrets.es.md)
- [09 — Cloud Storage](10_storage.es.md)
- [10 — Service Accounts e IAM](11_iam.es.md)
- [11 — Cloud Run](12_cloud_run.es.md)
- [12 — Cloud Tasks y Scheduler](13_tasks.es.md)
- [13 — Dockerfile](14_dockerfile.es.md)
- [14 — Primer Despliegue](15_first_deploy.es.md)
- 15 — Dominio personalizado y SSL (Capítulo actual)
- [16 — Workload Identity Federation](17_wif.es.md)
- [17 — GitHub Actions CI/CD](18_github_actions.es.md)
- [18 — Referencia Rápida](19_quick_reference.es.md)
