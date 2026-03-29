---
description: "Mapea tu dominio personalizado y provisiona automáticamente un certificado SSL gestionado para tu servicio en Cloud Run."
image: assets/social-banner.png

---
# 08 — Dominio Personalizado y SSL

← [Anterior: 07 — Primer Despliegue](07_first_deploy.md)

> 💰 **El registro del dominio cuesta dinero — se paga a tu registrador, no a GCP.**
> Un dominio `.cl` cuesta aproximadamente $10–20/año dependiendo del registrador (NIC.cl cobra ~$12/año). El dominio es tuyo independientemente de qué hosting uses.
>
> ✅ **Todo lo demás en este capítulo es gratuito.** El mapeo de dominio en GCP, la provisión del certificado SSL y su renovación automática son todos gratuitos. El plan gratuito de Cloudflare para DNS y protección DDoS también es gratuito.

## Lo que Cloud Run proporciona por defecto

Después de desplegar, Cloud Run te da una URL como:
```
https://mycoolproject-abc123-uc.a.run.app
```

Esta URL ya tiene HTTPS con un certificado SSL gestionado por Google. Para producción quieres usar tu propio dominio (`mycoolproject.cl`).

## Cómo funciona SSL aquí

La titularidad del SSL depende de cómo configures tu DNS. Hay dos opciones:

| Configuración | Quién gestiona el SSL | Consideraciones |
|---|---|---|
| **Cloudflare solo DNS (nube gris)** | **GCP / Cloud Run** | Google provisiona y renueva automáticamente tu certificado de forma gratuita. Sin intermediarios. Esto es lo que usa esta guía. |
| **Cloudflare con proxy (nube naranja)** | **Cloudflare** | Cloudflare termina el SSL y re-cifra el tráfico hacia GCP. Agrega el WAF y la protección DDoS de Cloudflare. Más complejo de configurar correctamente — necesitas establecer el modo SSL de Cloudflare en "Full (strict)" o tendrás bucles de redirección. |

Esta guía usa **solo DNS** — Cloud Run lo maneja todo. GCP habla directamente con el DNS de tu dominio, provisiona un certificado gratuito a través de Google Trust Services y termina todo el SSL en el borde de Cloud Run. Sin Certbot, sin nginx, sin gestión de certificados necesaria.

---

## Mapear tu dominio a Cloud Run

```bash
# Mapea tu dominio personalizado al servicio de Cloud Run e inicia la provisión del certificado SSL.
# Después de ejecutar esto, GCP te dirá qué registro DNS agregar en tu registrador.
# Resultado: GCP imprime el registro CNAME o A requerido — agrégalo a tu proveedor de DNS.
gcloud run domain-mappings create \
  --service=mycoolproject \
  --domain=mycoolproject.cl \
  --region=southamerica-east1
```

Esto retorna un registro DNS para agregar — algo como:

```
Agrega un registro CNAME:
  mycoolproject.cl → ghs.googlehosted.com
```

O un registro A apuntando a la IP de Google. El registro exacto depende de si es un dominio raíz o un subdominio.

Verifica el estado (la provisión SSL tarda desde unos minutos hasta una hora):

```bash
# Verifica el estado del mapeo de dominio y la provisión del certificado SSL.
# Espera hasta que certificateMode muestre AUTOMATIC y mappingStatus muestre ACTIVE.
# La provisión SSL tarda desde unos minutos hasta una hora después de que el DNS se propague.
gcloud run domain-mappings describe \
  --domain=mycoolproject.cl \
  --region=southamerica-east1
```

Espera hasta que `certificateMode` muestre `AUTOMATIC` y `mappingStatus` muestre `ACTIVE`.

---

## Configuración de DNS (en tu registrador o Cloudflare)

Si usas **Cloudflare** (recomendado — protección DDoS gratuita, filtrado de bots):

1. Agrega tu dominio a Cloudflare (plan gratuito)
2. Apunta los nameservers de tu registrador a los de Cloudflare
3. En el DNS de Cloudflare, agrega el registro que GCP te proporcionó
4. Establece el proxy en **Solo DNS (nube gris)** ☁️

> **¿Por qué nube gris?** Cuando estableces el registro en "Solo DNS", Cloudflare actúa como un resolvedor de DNS puro — simplemente le dice a los navegadores dónde está tu servidor. GCP maneja entonces el certificado SSL directamente con tu dominio. Si habilitas la nube naranja (proxy), Cloudflare intercepta todo el tráfico e intenta terminar SSL por su cuenta, lo que rompe la provisión del certificado de GCP y causa errores `SSL_ERROR_RX_RECORD_TOO_LONG` en el navegador.
>
> Igual obtienes la **protección DDoS** y el **filtrado de bots** de Cloudflare en el plan gratuito con el modo solo DNS — simplemente funciona en la capa de red en lugar de la capa de aplicación.

Si usas tu registrador directamente (NIC.cl, Namecheap, etc.):

1. Inicia sesión en el panel de gestión de DNS de tu registrador
2. Agrega el registro CNAME o A que GCP proporcionó

---

## Redirección www

Para también manejar `www.mycoolproject.cl`:

```bash
# Mapea el subdominio www al mismo servicio, para que www.mycoolproject.cl también funcione.
gcloud run domain-mappings create \
  --service=mycoolproject \
  --domain=www.mycoolproject.cl \
  --region=southamerica-east1
```

O agrega un `CNAME www → mycoolproject.cl` en tu DNS y deja que Cloudflare/el registrador maneje la redirección.

---

## Actualizar ALLOWED_HOSTS

Una vez que el dominio esté activo, actualiza el servicio de Cloud Run para incluir tanto el dominio personalizado como la URL original `.run.app`:

```bash
# Actualiza la variable de entorno ALLOWED_HOSTS en el servicio en ejecución sin un despliegue completo.
# Django rechaza solicitudes con un encabezado Host no reconocido — esto previene ese error 400.
# Cloud Run crea automáticamente una nueva revisión cuando cambian las variables de entorno.
gcloud run services update mycoolproject \
  --region=southamerica-east1 \
  --update-env-vars=ALLOWED_HOSTS="mycoolproject.cl,www.mycoolproject.cl"
```

`ALLOWED_HOSTS` es la configuración de seguridad de Django que rechaza solicitudes con un encabezado `Host` no reconocido — previene ataques de encabezado HTTP Host.

---

## 📖 Navegación

- [01 — Configuración del Proyecto GCP](01_gcp_setup.es.md)
- [02 — Artifact Registry](02_artifact_registry.es.md)
- [03 — Cloud SQL (Base de datos PostgreSQL)](03_cloud_sql.es.md)
- [04 — Secret Manager](04_secret_manager.es.md)
- [05 — Cloud Storage (Media & static files)](05_cloud_storage.es.md)
- [06 — Dockerfile](06_dockerfile.es.md)
- [07 — Primer Despliegue](07_first_deploy.es.md)
- 08 — Dominio Personalizado y SSL (Capítulo actual)
- [09 — Workload Identity Federation (Auth de GitHub sin llaves)](09_workload_identity.es.md)
- [10 — Pipeline CI/CD con GitHub Actions](10_github_actions.es.md)
- [11 — Referencia Rápida](11_quick_reference.es.md)
- [12 — Bonus: Email Personalizado (@dominio.cl)](12_custom_email.es.md)
