# C&K Ingenieros — Handover

Corporate website for **CYK Ingeniería y Construcción Eléctrica SpA** (cykingenieros.cl).
Static site (HTML/CSS/JS) + one PHP form relay, hosted on Hostinger Premium Web Hosting.
Branch with all work: `claude/modest-ramanujan-1l04je`.

## Pages (all built, approved copy in Spanish es-CL)
Inicio `/`, Nosotros `/nosotros/`, Servicios `/servicios/`, Proyectos `/proyectos/`,
Contacto `/contacto/`, Política de Privacidad `/politica-de-privacidad/` (placeholder Lorem Ipsum).

## How the code is organised
| Path | What it is |
|---|---|
| `_build/*.template.html` | One template per page (home, nosotros, servicios, proyectos, contacto, privacidad). **Edit page content here.** |
| `_build/partials/` | Shared pieces used by every page: `head.html`, `header.html`, `footer.html`, `form.html`, `style.css`, `script.js`. |
| `_build/build.py` | Build script. Data lists at the top: `SERVICES`, `PROJECTS`, `CLIENTS`, `TEAM`, `PAGES`, `FORM_PRIVACY`. |
| `_build/photos/`, `_build/clients/` | Source images (stock photos are free Unsplash placeholders; `prj-1..3` are real C&K photos). |
| `_build/static/` | `robots.txt`, `.htaccess`, deploy notes copied into `dist/`. |
| `api/contacto.php` | Form relay → GoHighLevel inbound webhook. URL goes in `api/config.php` (git-ignored). See `api/README.md`. |
| `dist/` | **Production site — upload its contents to Hostinger `public_html/`.** Generated, do not edit by hand. |
| `index.html`, `nosotros/`, … in repo root | Single-file previews (images inlined) used only for claude.ai previews. Do not upload. |

Placeholders like `{{ARROW}}`, `{{IMG:hero}}`, `{{FORM}}` in templates are filled by `build.py`.

## Rebuild after any change
```bash
pip install pillow numpy      # once
python3 _build/build.py --prod   # production site in dist/  (WebP images <= 100 KB)
python3 _build/build.py          # optional: single-file previews in repo root
```
Never edit files in `dist/` or the root page folders directly — they are overwritten on build.

## Design system (keep consistent)
- Colours (CSS variables in `_build/partials/style.css`): navy `#081E47`, gold `#D7B257`, gold text on white `#8A6A1E`, light grey `#F4F5F8`.
- Font: Hanken Grotesk (Google Fonts). Pill-shaped buttons with a round arrow; rounded cards (`--r-lg: 28px`).
- No decorative diagrams/line art — client explicitly rejected them. Use real photos.
- Sections alternate white / light grey / navy. Eyebrow label + large heading + lead paragraph pattern.
- Reveal-on-scroll via `data-reveal` and `style="--d:<ms>"`; respects reduced motion.

## Common edits
- **Team job titles:** `TEAM` list in `_build/build.py` — replace `None` with the title, e.g. `"Jefe de Proyectos"`.
- **Privacy policy text:** `_build/privacidad.template.html` (remove the `.doc__note` "Texto provisional" block).
- **Add a project:** add an `<article class="pj">` block in `_build/proyectos.template.html` and, for the homepage cards, an entry in `PROJECTS`.
- **Client logos:** transparent PNG in `_build/clients/`, then add to `CLIENTS`.
- **Replace a stock photo:** overwrite the file in `_build/photos/` with the same name and rebuild.

## Deploy (Hostinger)
1. hPanel → Websites → cykingenieros.cl → Files → File Manager → "Access files of cykingenieros.cl" → `public_html/`.
2. Delete Hostinger's default placeholder files there (e.g. `default.php`, `index.php`) if present.
3. Upload the **contents** of `dist/` (or `cyk-sitio-dist.zip` and Extract), including hidden `.htaccess` files.
4. In `public_html/api/`, copy `config.example.php` → `config.php`, paste the GoHighLevel webhook URL.
5. hPanel → Security → SSL → Force HTTPS. Do **not** change DNS/MX (company email is on Microsoft 365).

## Pending from client
Privacy policy text · team job titles (and surname spellings) · GoHighLevel webhook URL ·
real C&K photos to replace stock images · confirmation that client names/logos may be published.
