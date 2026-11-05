"""Build the standalone site pages from _build/*.template.html + _build/partials/.

Optimizes the repository images and the photos in _build/photos/ and inlines
them as base64 data URIs, so the output is a single self-contained HTML file.

Photos in _build/photos/ are free-licence Unsplash images used as references
until C&K supplies its own project photography.

Usage:
  python3 _build/build.py          single-file previews (images inlined) in the repo root
  python3 _build/build.py --prod   production site in dist/ for Hostinger public_html/:
                                   WebP images (each <= 100 KB) in assets/img, shared CSS/JS
                                   as cached files, robots.txt, sitemap.xml, .htaccess, api/
"""
import base64
import hashlib
import re
import io
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
PARTIALS = BUILD / "partials"
PROD = "--prod" in sys.argv
OUT_ROOT = ROOT / "dist" if PROD else ROOT
SITE = "https://cykingenieros.cl"
IMG_DIR = OUT_ROOT / "assets" / "img"
MAX_IMG_BYTES = 100 * 1024
_emitted = {}

ARROW = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" '
         'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8h10M9 4l4 4-4 4"/></svg>')

PIN = ('<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 14.5s4.5-4.2 4.5-7.7A4.5 4.5 0 0 0 3.5 6.8'
       'c0 3.5 4.5 7.7 4.5 7.7Z"/><circle cx="8" cy="6.8" r="1.6"/></svg>')
CHECK = '<svg viewBox="0 0 12 12" aria-hidden="true"><path d="m2.2 6.3 2.4 2.4L9.8 3.5"/></svg>'

# name -> output width
PHOTO_WIDTHS = {"hero": 2000, "approach": 1200, "svc-tarifaria": 1100, "nos-hero": 1400,
                "nos-filosofia": 1100, "nos-confidencialidad": 1100,
                "svc-mantencion": 1000, "svc-mantencion-2": 1100}

SERVICES = [
    ("asesoria-tecnica", "svc-asesoria", "Equipo técnico revisando una obra en terreno",
     "Asesoría técnica y representación",
     "Acompañamiento personalizado, análisis de discrepancias y representación del cliente en reuniones técnicas, con independencia de criterio y respaldo técnico."),
    ("ingenieria-de-diseno", "svc-diseno", "Ingeniero trabajando sobre planos",
     "Ingeniería de diseño",
     "Desarrollo de proyectos eléctricos mediante levantamientos en terreno, planimetría y coordinación con las distintas especialidades."),
    ("construccion-electrica", "svc-construccion", "Técnica eléctrica trabajando en altura con equipo de seguridad",
     "Construcción eléctrica",
     "Ejecución de proyectos eléctricos propios o entregados por el cliente, con planificación, supervisión y rigor técnico en cada detalle."),
    ("mantencion-especializada", "svc-mantencion", "Tablero eléctrico con protecciones y cableado",
     "Mantención especializada",
     "Mantenciones preventivas, predictivas y correctivas, planificadas según el estado y la criticidad de cada instalación."),
    ("equipos-alta-complejidad", "svc-equipos", "Pabellón con equipamiento médico de alta complejidad",
     "Instalación de equipos de alta complejidad",
     "Habilitación e instalación eléctrica para equipos médicos e industriales, considerando sus requerimientos técnicos y la coordinación con proveedores."),
    ("diagnostico-tecnico", "svc-diagnostico", "Técnico realizando mediciones eléctricas",
     "Equipos y diagnóstico técnico",
     "Mediciones, termografía y análisis de variables eléctricas para investigar fallas, evaluar instalaciones y fundamentar decisiones."),
]

PROJECTS = [
    # (photo, slug, sector, title, client, location, description, alt) — real C&K projects
    # from the previous website; photos supplied by the client.
    ("prj-1", "esterilizacion-clinica-meds", "Infraestructura clínica", "Proyecto de Esterilización",
     "Clínica MEDS", "Lo Barnechea, RM",
     "Suministro, instalación y conexión del tablero de esterilización a la barra general de la clínica.",
     "Técnico de C&amp;K trabajando en altura durante el Proyecto de Esterilización de Clínica MEDS"),
    ("prj-2", "bureau-veritas-calama", "Media tensión", "Proyecto Bureau Veritas Calama",
     "Bureau Veritas Laboratorio Minero", "Calama, Antofagasta",
     "Diseño y construcción de empalme en media tensión, con conexión de 1,6 MVA.",
     "Estructuras de media tensión del empalme construido para Bureau Veritas en Calama"),
    ("prj-3", "hospital-mutual-alameda", "Climatización hospitalaria", "Proyecto Hospital Mutual Alameda",
     "Mutual de Seguridad", "Estación Central, RM",
     "Diseño, construcción y conexión de la nueva central de climatización Daikin.",
     "Central de climatización Daikin instalada en la azotea del Hospital Mutual Alameda"),
]


def b64(data: bytes, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(data).decode()


def webp_bytes(img: Image.Image) -> bytes:
    """Encode as WebP, lowering quality (then size) until the file is <= 100 KB."""
    img = img.convert("RGBA") if img.mode in ("RGBA", "LA", "P") else img.convert("RGB")
    while True:
        for q in (82, 76, 70, 64, 58, 52):
            buf = io.BytesIO()
            img.save(buf, "WEBP", quality=q, method=6)
            if buf.tell() <= MAX_IMG_BYTES:
                return buf.getvalue()
        img = img.resize((int(img.width * .85), int(img.height * .85)), Image.LANCZOS)


def emit(img: Image.Image, name: str) -> str:
    """Production: write assets/img/<name>.webp once and return its URL."""
    if name not in _emitted:
        data = webp_bytes(img)
        IMG_DIR.mkdir(parents=True, exist_ok=True)
        (IMG_DIR / f"{name}.webp").write_bytes(data)
        _emitted[name] = f"/assets/img/{name}.webp"
    return _emitted[name]


def slug(text: str) -> str:
    import unicodedata
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def jpeg(img: Image.Image, quality=72, name=None) -> str:
    if PROD:
        return emit(img, name or "img-" + hashlib.sha1(img.tobytes()).hexdigest()[:10])
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return b64(buf.getvalue(), "image/jpeg")


def png(img: Image.Image, name=None) -> str:
    if PROD:
        return emit(img, name or "img-" + hashlib.sha1(img.tobytes()).hexdigest()[:10])
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return b64(buf.getvalue(), "image/png")


def resize(img, w):
    if img.width <= w:
        return img
    return img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)


def logos():
    logo = Image.open(ROOT / "Transparente.png").convert("RGBA")
    logo = resize(logo.crop(logo.getbbox()), 640)
    a = np.array(logo).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    indigo = (b > r + 20) & (b > g)  # wordmark + mark strokes -> white for dark backgrounds
    # All-white version for dark backgrounds (the client's "Logo editable-04" is a
    # white logo saved as JPG, so it carries no usable pixels): the round mark becomes
    # solid white with its interlocking strokes knocked out, the wordmark turns white.
    split = int(logo.height * 0.58)  # wordmark sits below the round mark
    white = a.copy()
    white[..., 0:3] = 255
    knock = indigo.copy()
    knock[split:, :] = False
    white[knock, 3] = 0
    white = Image.fromarray(white.astype("uint8"))
    if PROD:
        return png(logo, "logo-cyk"), png(white, "logo-cyk-blanco")
    q = lambda im: im.quantize(colors=96, method=Image.Quantize.FASTOCTREE)
    return png(q(logo)), png(q(white))


def favicon():
    """Square icon from the round C&K mark (top part of the logo)."""
    logo = Image.open(ROOT / "Transparente.png").convert("RGBA")
    logo = logo.crop(logo.getbbox())
    mark = logo.crop((0, 0, logo.width, int(logo.height * 0.55)))
    mark = mark.crop(mark.getbbox())
    side = max(mark.size)
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.alpha_composite(mark, ((side - mark.width) // 2, (side - mark.height) // 2))
    sq = sq.resize((64, 64), Image.LANCZOS)
    buf = io.BytesIO()
    sq.save(buf, "PNG", optimize=True)
    if PROD:
        (OUT_ROOT / "favicon.png").write_bytes(buf.getvalue())
        return "/favicon.png"
    return b64(buf.getvalue(), "image/png")


def photo(name):
    img = Image.open(BUILD / "photos" / f"{name}.jpg")
    return jpeg(resize(img, PHOTO_WIDTHS.get(name, 900)), name=name)


def services_html():
    out = []
    for i, (anchor, img, alt, title, desc) in enumerate(SERVICES):
        out.append(
            f'<li class="svc" data-reveal style="--d:{(i % 3) * 90}">'
            f'<div class="svc__media"><img src="{photo(img)}" alt="{alt}" width="900" height="600" loading="lazy"></div>'
            f'<div class="svc__body"><h3>{title}</h3><p>{desc}</p>'
            f'<a class="link" href="/servicios/#{anchor}">Conocer especialidad {ARROW}</a></div></li>'
        )
    return "\n      ".join(out)


def projects_html():
    out = []
    for i, (img, slug, sector, title, client, place, desc, alt) in enumerate(PROJECTS):
        out.append(
            f'<li class="prj" data-reveal style="--d:{i * 90}">'
            f'<div class="prj__media"><span class="prj__badge">{place}</span>'
            f'<img src="{photo(img)}" alt="{alt}" width="460" height="610" loading="lazy"></div>'
            f'<div class="prj__body"><span class="prj__sector">{sector}</span>'
            f'<h3>{title}</h3><span class="prj__client">{client}</span>'
            f'<p>{desc}</p>'
            f'<a class="link" href="/proyectos/#{slug}">Ver proyecto {ARROW}</a></div></li>'
        )
    return "\n      ".join(out)


CLIENTS = [
    ("clinica-meds", "Clínica Meds"),
    ("almarza", "Perfiles y Tubos de Acero Almarza"),
    ("corteva", "Corteva Agriscience"),
    ("lourdes", "Lourdes Bulk Wine"),
    ("veramonte", "Viñedos Veramonte"),
]


def client_logos(repeat=False):
    """Approved client logos (grey-tinted in CSS). repeat=True renders a decorative,
    screen-reader-hidden copy used to keep the marquee wider than the viewport."""
    out = []
    for key, name in CLIENTS:
        img = Image.open(BUILD / "clients" / f"{key}.png").convert("RGBA")
        img = img.resize((round(img.width * 110 / img.height), 110), Image.LANCZOS) if img.height > 110 else img
        img = Image.merge("LA", (Image.new("L", img.size, 0), img.getchannel("A")))  # colour comes from CSS
        alt = "" if repeat else name
        hidden = ' aria-hidden="true"' if repeat else ""
        out.append(f'<li{hidden}><img src="{png(img, "cliente-" + key)}" alt="{alt}" width="{img.width}" height="{img.height}" loading="lazy"></li>')
    return "".join(out)


TEAM = [
    # (file, name, role). Karen first; other roles pending confirmation from C&K.
    ("Fotografia Karen Rodriìguez.jpg", "Karen Rodríguez", "Gerenta General"),
    ("Fotos-Equipo/10.Dani png.png", "Dani", None),
    ("Fotos-Equipo/11.Natypng.png", "Naty", None),
    ("Fotos-Equipo/3.Rubenpng.png", "Rubén", None),
    ("Fotos-Equipo/4.Francisco png.png", "Francisco", None),
    ("Fotos-Equipo/5.Hector png.png", "Héctor", None),
    ("Fotos-Equipo/7.Marcopng.png", "Marco", None),
    ("Fotos-Equipo/8.Claudio png.png", "Claudio", None),
]


def portrait(path, name, w=560):
    """Crop a portrait to 4:5 (keeping the head near the top) and encode it."""
    img = Image.open(ROOT / path).convert("RGB")
    target = img.width * 5 / 4
    if img.height > target:
        top = int((img.height - target) * 0.15)
        img = img.crop((0, top, img.width, top + int(target)))
    return jpeg(resize(img, w), 78, name="equipo-" + slug(name))


def team_html():
    out = []
    for i, (path, name, role) in enumerate(TEAM):
        role_html = (f'<span class="member__role">{role}</span>' if role
                     else '<span class="member__role member__role--pending">Cargo por confirmar</span>')
        lead = " member--lead" if i == 0 else ""
        out.append(
            f'<li class="member{lead}" data-reveal style="--d:{(i % 4) * 80}">'
            f'<div class="member__photo"><img src="{portrait(path, name)}" alt="{name}, C&amp;K Ingenieros" '
            f'width="560" height="700" loading="lazy"></div>'
            f'<h3>{name}</h3>{role_html}</li>'
        )
    return "\n      ".join(out)


FORM_PRIVACY = {
    "default": 'Tratamos cada consulta y sus antecedentes técnicos y comerciales con reserva y discreción, '
               'conforme a nuestra <a href="/politica-de-privacidad/">Política de Privacidad</a>.',
    "contacto": 'Tus datos serán utilizados para responder y gestionar tu solicitud, de acuerdo con nuestra '
                '<a href="/politica-de-privacidad/">Política de Privacidad</a>.',
}

PAGES = [
    # (template, output, path, nav key, header CTA href, title, description)
    ("home", "index.html", "/", "inicio", "#contacto",
     "C&amp;K Ingenieros — Asesoría, Ingeniería y Construcción Eléctrica",
     "Ingeniería eléctrica especializada: asesoría técnica, ingeniería de diseño, construcción eléctrica, "
     "mantención y diagnóstico para salud, industria y agro. Rigor y precisión en cada proyecto."),
    ("nosotros", "nosotros/index.html", "/nosotros/", "nosotros", "/contacto/",
     "Nosotros — C&amp;K Ingenieros",
     "Empresa chilena de ingeniería y construcción eléctrica. Experiencia técnica, atención personalizada "
     "y una metodología de trabajo basada en evidencia: levantar, analizar, resolver y verificar."),
    ("servicios", "servicios/index.html", "/servicios/", "servicios", "/contacto/",
     "Servicios — C&amp;K Ingenieros",
     "Asesoría técnica y representación, ingeniería de diseño, construcción eléctrica, mantención "
     "especializada, instalación de equipos de alta complejidad, diagnóstico técnico y asesoría tarifaria."),
    ("proyectos", "proyectos/index.html", "/proyectos/", "proyectos", "/contacto/",
     "Proyectos — C&amp;K Ingenieros",
     "Proyectos eléctricos ejecutados por C&amp;K Ingenieros: infraestructura clínica, instalaciones "
     "industriales y media tensión, de Lo Barnechea a Calama."),
    ("contacto", "contacto/index.html", "/contacto/", "contacto", "#formulario",
     "Contacto — C&amp;K Ingenieros",
     "Solicita una evaluación especializada a C&amp;K Ingenieros. Escríbenos a contacto@cykingenieros.cl "
     "o por WhatsApp al +56 9 8751 2250. Atención directa y reservada."),
    ("privacidad", "politica-de-privacidad/index.html", "/politica-de-privacidad/", "privacidad", "/contacto/",
     "Política de Privacidad — C&amp;K Ingenieros",
     "Política de Privacidad de CYK Ingeniería y Construcción Eléctrica SpA: tratamiento y resguardo de "
     "los datos personales y la información técnica y comercial de clientes."),
]


def build_page(tpl, out, path, nav, cta, title, desc, shared):
    html = (BUILD / f"{tpl}.template.html").read_text(encoding="utf-8")
    if "{{FORM}}" in html:
        html = html.replace("{{FORM}}", shared["FORM"]).replace("{{FORM_PRIVACY}}", FORM_PRIVACY.get(nav, FORM_PRIVACY["default"]))
    for key in ("HEAD", "HEADER", "FOOTER"):
        html = html.replace("{{%s}}" % key, shared[key])
    if PROD:
        html = (html.replace("<style>\n{{CSS}}", '<link rel="stylesheet" href="/assets/css/site.css">\n<style>')
                    .replace("<script>\n{{SCRIPT}}", '<script src="/assets/js/site.js"></script>\n<script>')
                    .replace("<script></script>\n", ""))
        html = html.replace("</head>", f'<meta property="og:image" content="{SITE}/assets/img/og-cyk.jpg">\n</head>', 1)
    html = html.replace("{{CSS}}", shared["CSS"]).replace("{{SCRIPT}}", shared["SCRIPT"])
    html = html.replace("{{FAVICON}}", shared["FAVICON"])
    html = (html.replace("{{TITLE}}", title).replace("{{DESC}}", desc)
                .replace("{{PATH}}", path).replace("{{CTA_HREF}}", cta))
    html = re.sub(r"\{\{CUR:(\w+)\}\}", lambda m: ' aria-current="page"' if m.group(1) == nav else "", html)
    if "{{SERVICES}}" in html:
        html = html.replace("{{SERVICES}}", services_html())
    if "{{TEAM}}" in html:
        html = html.replace("{{TEAM}}", team_html())
    if "{{PROJECTS}}" in html:
        html = html.replace("{{PROJECTS}}", projects_html())
    if "{{LOGO_SLOTS}}" in html:
        html = (html.replace("{{LOGO_SLOTS_REPEAT}}", client_logos(repeat=True))
                    .replace("{{LOGO_SLOTS}}", client_logos()))
    html = html.replace("{{PIN}}", PIN).replace("{{CHECK}}", CHECK)
    html = (html.replace("{{LOGO_WHITE}}", shared["LOGO_WHITE"]).replace("{{LOGO}}", shared["LOGO"])
                .replace("{{ARROW}}", ARROW))
    if "{{KAREN}}" in html:
        html = html.replace("{{KAREN}}", shared["KAREN"])
    html = re.sub(r"\{\{IMG:([\w-]+)\}\}", lambda m: photo(m.group(1)), html)
    assert "{{" not in html, html[html.index("{{"):html.index("{{") + 40]
    dest = OUT_ROOT / out
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({dest.stat().st_size / 1024:.0f} KB)")


def main():
    if PROD:
        if OUT_ROOT.exists():
            shutil.rmtree(OUT_ROOT)
        OUT_ROOT.mkdir()
    logo, logo_white = logos()
    shared = {
        "HEAD": (PARTIALS / "head.html").read_text(encoding="utf-8"),
        "HEADER": (PARTIALS / "header.html").read_text(encoding="utf-8"),
        "FOOTER": (PARTIALS / "footer.html").read_text(encoding="utf-8"),
        "FORM": (PARTIALS / "form.html").read_text(encoding="utf-8"),
        "CSS": (PARTIALS / "style.css").read_text(encoding="utf-8"),
        "SCRIPT": (PARTIALS / "script.js").read_text(encoding="utf-8"),
        "LOGO": logo, "LOGO_WHITE": logo_white,
        "KAREN": jpeg(resize(Image.open(ROOT / "Fotografia Karen Rodriìguez.jpg"), 680), 80, name="karen-rodriguez"),
    }
    shared["FAVICON"] = favicon()
    for page in PAGES:
        if (BUILD / f"{page[0]}.template.html").exists():
            build_page(*page, shared)
    if PROD:
        write_production_extras(shared)


def write_production_extras(shared):
    css_dir, js_dir = OUT_ROOT / "assets" / "css", OUT_ROOT / "assets" / "js"
    css_dir.mkdir(parents=True, exist_ok=True)
    js_dir.mkdir(parents=True, exist_ok=True)
    (css_dir / "site.css").write_text(shared["CSS"], encoding="utf-8")
    (js_dir / "site.js").write_text(shared["SCRIPT"], encoding="utf-8")
    # Link-preview image (1200x630) for social sharing.
    og = Image.open(BUILD / "photos" / "hero.jpg").convert("RGB")
    og = og.resize((1200, round(og.height * 1200 / og.width)), Image.LANCZOS)
    top = (og.height - 630) // 2
    og.crop((0, top, 1200, top + 630)).save(IMG_DIR / "og-cyk.jpg", quality=80, optimize=True, progressive=True)
    # api/ (form relay) without the server-only config.
    shutil.copytree(ROOT / "api", OUT_ROOT / "api", ignore=shutil.ignore_patterns("config.php", "README.md"))
    for f in ("robots.txt", ".htaccess", "LEEME-DESPLIEGUE.md"):
        shutil.copy(BUILD / "static" / f, OUT_ROOT / f)
    urls = "".join(f"  <url><loc>{SITE}{p[2]}</loc></url>\n" for p in PAGES)
    (OUT_ROOT / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "</urlset>\n", encoding="utf-8")
    total = sum(f.stat().st_size for f in OUT_ROOT.rglob("*") if f.is_file())
    imgs = sorted(IMG_DIR.glob("*.webp"), key=lambda f: -f.stat().st_size)
    print(f"dist/: {len(imgs)} WebP images, largest {imgs[0].name} {imgs[0].stat().st_size / 1024:.0f} KB; "
          f"total site {total / 1024:.0f} KB")


if __name__ == "__main__":
    main()
