# Despliegue en Hostinger — C&K Ingenieros

Esta carpeta (`dist/`) es el sitio listo para publicar. Se genera con:

```bash
python3 _build/build.py --prod
```

## Subir

1. hPanel → **Archivos → Administrador de archivos** → `public_html/`.
2. Sube **todo el contenido** de `dist/` (no la carpeta en sí), incluidos los archivos ocultos `.htaccess` y `api/.htaccess`.
3. En `public_html/api/`, copia `config.example.php` como `config.php` y pega la URL del webhook de GoHighLevel (ver `api/README.md` en el repositorio).
4. hPanel → **Seguridad → SSL**: activa el certificado y **Forzar HTTPS**.

No es necesario modificar DNS, MX ni registros de correo (Microsoft 365 sigue igual).

## Contenido

| Ruta | Descripción |
|---|---|
| `index.html`, `nosotros/`, `servicios/`, `proyectos/`, `contacto/`, `politica-de-privacidad/` | Páginas |
| `assets/img/*.webp` | Imágenes en WebP, cada una ≤ 100 KB |
| `assets/css/site.css`, `assets/js/site.js` | Estilos y scripts compartidos (en caché) |
| `api/contacto.php` | Envío del formulario a GoHighLevel |
| `robots.txt`, `sitemap.xml` | SEO |
| `.htaccess` | Compresión, caché y cabeceras de seguridad |

Tras publicar, envía `https://cykingenieros.cl/sitemap.xml` en Google Search Console.
