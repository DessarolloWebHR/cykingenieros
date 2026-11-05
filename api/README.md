# Formulario de contacto → GoHighLevel

Los formularios de **Inicio** y **Contacto** envían sus datos a `api/contacto.php`, que los valida y los reenvía al webhook entrante de GoHighLevel. La URL del webhook se guarda solo en el servidor; nunca aparece en el código del navegador.

## 1. Crear el webhook en GoHighLevel

1. **Automation → Workflows → Create Workflow → Start from scratch.**
2. Trigger: **Inbound Webhook**. Copia la URL que muestra.
3. Envía una solicitud de prueba desde el sitio (paso 3) y luego pulsa **Fetch Sample Requests** para que GoHighLevel reconozca los campos.
4. Agrega la acción **Create/Update Contact** y asigna los campos:

   | Campo enviado | Campo en GoHighLevel |
   |---|---|
   | `first_name` | First Name |
   | `last_name` | Last Name |
   | `email` | Email |
   | `company_name` | Company Name |
   | `especialidad` | Campo personalizado (p. ej. "Especialidad requerida") |
   | `mensaje` | Campo personalizado o nota |
   | `source` | Source ("Sitio web cykingenieros.cl") |
   | `pagina` | Página desde la que se envió (`/` o `/contacto/`) |

5. Opcional: agrega una notificación interna (correo o WhatsApp a Karen) y una etiqueta como `web-lead`. Publica el workflow.

## 2. Configurar el servidor (Hostinger)

1. Sube el contenido del sitio a `public_html/` (incluida la carpeta `api/`).
2. En `public_html/api/`, copia `config.example.php` como `config.php` y pega la URL del webhook en `ghl_webhook_url`.
3. `config.php` está bloqueado para acceso web (`api/.htaccess`) y excluido del repositorio (`.gitignore`).

## 3. Probar

Envía el formulario en `https://cykingenieros.cl/contacto/`. Debe aparecer "Gracias por contactarnos." y el contacto debe crearse en GoHighLevel.

## Protección anti-spam

- Campo trampa invisible y tiempo mínimo de 2,5 s en la página (navegador y servidor).
- Máximo 5 envíos por IP cada 10 minutos.
- Validación de campos y de la especialidad seleccionada en el servidor.
