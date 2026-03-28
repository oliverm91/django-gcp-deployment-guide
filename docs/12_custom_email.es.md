---
description: "Aprenda a configurar direcciones de correo electrónico profesionales @dominio.cl y configure el correo electrónico transaccional para su aplicación Django a través de registros DNS en GCP y proveedores externos."
image: assets/social-banner.png
---
# 12 — Bonus: Email Personalizado (@dominio.cl)

← [Anterior: 11 — Referencia Rápida](11_quick_reference.md)

Tener un correo electrónico personalizado como `info@mycoolproject.cl` es esencial para la credibilidad. Hay dos tipos de configuraciones de correo electrónico que necesita:

1.  **Correo Electrónico Profesional (Bandeja de entrada):** Para que usted envíe/reciba correo (como Gmail pero para su dominio).
2.  **Correo Electrónico Transaccional (SMTP):** Para que la aplicación Django envíe correos electrónicos automáticos (restablecimiento de contraseñas, notas de bienvenida).

## ¿Por qué no hay un menú de "Email" en GCP?

Uno de los puntos de confusión más comunes: **GCP no proporciona un servicio de alojamiento de correo nativo** (como Amazon SES). En su lugar, Google ofrece **Google Workspace** (como un servicio empresarial separado) o se asocia con proveedores externos como **SendGrid/Brevo**.

### La trampa del Puerto 25
Google Cloud **bloquea el tráfico saliente en el puerto 25** para todos los recursos de Cloud Run y Compute Engine para evitar el spam.
- **No puede** usar el puerto 25.
- **DEBE** usar el puerto **587** (TLS) o **465** (SSL) en su configuración de Django.
- No existe una "regla de Firewall" para desbloquear el puerto 25 para cuentas estándar.

---

## 1. Correo Electrónico Profesional (Bandejas de entrada para humanos)

GCP no aloja buzones de correo. El estándar de la industria es **Google Workspace**.

### Configuración
1.  Regístrese en [workspace.google.com](https://workspace.google.com/).
2.  **Verificación del Dominio:** Google le pedirá que agregue un registro `TXT` a su DNS (Capítulo 08).
3.  **Registros MX:** Estos le dicen al mundo dónde entregar el correo. Debe agregar estos registros a su proveedor de DNS (Cloudflare/NIC.cl).

| Tipo | Host | Apunta a | Prioridad |
|---|---|---|---|
| MX | @ | `ASPMX.L.GOOGLE.COM` | 1 |
| MX | @ | `ALT1.ASPMX.L.GOOGLE.COM` | 5 |

---

## 2. Correo Electrónico Transaccional (Correo automatizado de la aplicación)

Google Cloud impide el envío de correo directamente desde Cloud Run a través del puerto 25 por seguridad. **Debe** utilizar un proveedor SMTP de terceros.

**Recomendación:** [Brevo](https://www.brevo.com/) (anteriormente Sendinblue) tiene un generoso nivel gratuito (300 correos electrónicos al día).

### Pasos de configuración:
1.  Cree una cuenta en Brevo y verifique su dominio.
2.  **Registros DKIM/SPF:** Brevo le dará registros `TXT`. Estas son "firmas" que prueban que el correo electrónico realmente vino de usted, evitando que vaya a SPAM.
3.  **Credenciales SMTP:** Brevo proporcionará un Servidor SMTP, Puerto, Usuario y Contraseña.

---

## 3. Actualizar los secretos de Django

Tome las credenciales SMTP de Brevo y agréguelas a **Secret Manager** (Capítulo 04):

```bash
# Actualice sus secretos con las credenciales de Brevo
echo -n "smtp-relay.brevo.com" | gcloud secrets versions add EMAIL_HOST --data-file=-
echo -n "587"                  | gcloud secrets versions add EMAIL_PORT --data-file=-
echo -n "su-usuario-brevo"     | gcloud secrets versions add EMAIL_HOST_USER --data-file=-
echo -n "su-password-brevo"    | gcloud secrets versions add EMAIL_HOST_PASSWORD --data-file=-
```

En su `web/core/settings/prod.py`, asegúrese de que estos estén conectados:

```python
# web/core/settings/prod.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'MyCoolProject <info@mycoolproject.cl>'
```

---

## 4. Por qué importan SPF y DKIM
Si no agrega estos registros DNS, es probable que Gmail y Outlook bloqueen sus correos electrónicos:
- **SPF:** Una "lista blanca" de servidores autorizados a enviar correo para su dominio.
- **DKIM:** Una firma criptográfica para cada correo electrónico.
- **DMARC:** Una política que les dice a otros qué hacer si fallan SPF/DKIM (generalmente "cuarentena" o "rechazo").

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
