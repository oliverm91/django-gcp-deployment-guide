---
description: "Aprenda sobre el registro de correos electrónicos personalizados, los costos involucrados y cómo configurar el envío de correos desde Django antes de configurar bandejas de entrada para humanos."
image: assets/social-banner.png
---
# 12 — Bonus: Email Personalizado (@dominio.cl)

← [Anterior: 11 — Referencia Rápida](11_quick_reference.es.md)

Una vez que tienes tu dominio (ej. `mycoolproject.cl`) del [Capítulo 08](08_domain_ssl.es.md), puedes crear cualquier dirección de correo bajo ese nombre (ej. `contacto@mycoolproject.cl`). No necesitas "registrar" cada dirección individualmente, pero sí necesitas configurar un servicio que las gestione.

---

## 1. Conceptos Básicos y Costos

### ¿Tengo que pagar por cada dirección?
Depende del uso:

- **Para la Aplicación (Envío automático):** Generalmente es **gratuito** para volúmenes bajos (ej. menos de 300 correos/día con Brevo). Puedes inventar cualquier dirección como `notificaciones@tu-dominio.cl` sin costo extra.
- **Para Humanos (Bandeja de entrada):** Si quieres entrar a una página tipo Gmail para leer y responder, generalmente es **pagado**. Google Workspace cobra ~$6 USD por usuario al mes.

### Configuración de Registros DNS

La identidad de correo electrónico se establece enteramente a través de su **proveedor de DNS** (Cloudflare o GCP Cloud DNS). Debe añadir estos registros para que otros servidores sepan cómo responderle y confíen en sus mensajes:

| Tipo | Nombre | Contenido / Valor | Propósito |
|---|---|---|---|
| **MX** | `@` | `aspmx.l.google.com` (ejemplo) | Entrega: "¿Hacia dónde redirijo el correo entrante?" |
| **TXT** | `@` | `v=spf1 include:_spf.google.com ~all` | Autenticidad: "¿Quién tiene permiso para enviar correos por mí?" |
| **TXT** | `google._domainkey` | `v=DKIM1; k=rsa; p=MIGfMA0GCS...` | Integridad: Una firma digital por correo. |
| **TXT** | `_dmarc` | `v=DMARC1; p=quarantine;` | Política: "¿Qué hacer si los demás fallan?" |

> 💡 **Nota:** Los valores de arriba son **ejemplos**. Los registros reales (especialmente los largos strings de DKIM) se los entregará el proveedor de correo que elija (Brevo, Google Workspace, etc.) en las siguientes secciones.

---

## 2. Envío de Correo desde la Aplicación (SMTP)

Esta es la prioridad para que tu Django pueda enviar confirmaciones de registro o recuperaciones de contraseña. GCP bloquea el puerto 25 obligatoriamente, por lo que **debes** usar un proveedor externo.

**Recomendación:** [Brevo](https://www.brevo.com/) (Gratis hasta 300 correos/día).

### Pasos:
1.  Crea una cuenta en el proveedor y añade tu dominio.
2.  **Registros SPF y DKIM (Crítico):** El proveedor te dará unos textos (registros TXT) que debes pegar en tu DNS. Estos son tu "firma digital" para que Gmail no mande tus correos a SPAM.
3.  **Configurar Django:** Usa las credenciales SMTP en tu **Secret Manager** (Capítulo 04) y conéctalas en `prod.py`.

---

## 3. Bandeja de entrada para Humanos (Opcional)

Si necesitas recibir correos de clientes y responderles como un profesional, necesitas un hosting de correo. El estándar es **Google Workspace**.

### Configuración con Google Workspace:
1.  **Verificación:** Google te pedirá un código TXT en tu DNS para probar que el dominio es tuyo.
2.  **Registros MX:** Estos registros le dicen a internet: "si alguien escribe a este dominio, entrega el mensaje a los servidores de Google".

| Tipo | Host | Valor | Prioridad |
|---|---|---|---|
| MX | @ | `ASPMX.L.GOOGLE.COM` | 1 |
| MX | @ | `ALT1.ASPMX.L.GOOGLE.COM` | 5 |

### Alternativa Gratuita: Email Forwarding
Si utilizas **Cloudflare**, puedes usar su servicio de **Email Forwarding** gratis:

1.  Habilita "Email Routing" en el dashboard de Cloudflare.
2.  Crea una regla: `info@mycoolproject.cl` → `tu-gmail-personal@gmail.com`.
3.  **Costo:** $0. Recibes los correos profesionales en tu bandeja personal. No puedes "responder como" el dominio fácilmente, pero es ideal para empezar.

---

## 4. ¿Por qué no hay un menú de "Email" en GCP?
Google prefiere que uses **Google Workspace** (que es un producto separado) o socios como SendGrid. En la consola de GCP **no verás** una opción para crear correos, todo se gestiona mediante registros DNS y credenciales SMTP externas.

---

## 📖 Navegación

- [01 — Configuración del Proyecto GCP](01_gcp_setup.es.md)
- [02 — Artifact Registry](02_artifact_registry.es.md)
- [03 — Cloud SQL (Base de datos PostgreSQL)](03_cloud_sql.es.md)
- [04 — Secret Manager](04_secret_manager.es.md)
- [05 — Cloud Storage (Media & static files)](05_cloud_storage.es.md)
- [06 — Dockerfile](06_dockerfile.es.md)
- [07 — Primer Despliegue](07_first_deploy.es.md)
- [08 — Dominio Personalizado y SSL](08_domain_ssl.es.md)
- [09 — Workload Identity Federation (Auth de GitHub sin llaves)](09_workload_identity.es.md)
- [10 — Pipeline CI/CD con GitHub Actions](10_github_actions.es.md)
- [11 — Referencia Rápida](11_quick_reference.es.md)
- 12 — Bonus: Email Personalizado (@dominio.cl) (Capítulo actual)
- [13 — Bonus: Django Tasks](13_django_tasks.es.md)
