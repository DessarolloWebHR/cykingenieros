"""Build the standalone site pages from _build/*.template.html + _build/partials/.

Optimizes the repository images and the photos in _build/photos/ and inlines
them as base64 data URIs, so the output is a single self-contained HTML file.

Photos in _build/photos/ are free-licence Unsplash images used as references
until C&K supplies its own project photography.

Usage:  python3 _build/build.py
"""
import base64
import re
import io
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
PARTIALS = BUILD / "partials"

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


def jpeg(img: Image.Image, quality=72) -> str:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
    return b64(buf.getvalue(), "image/jpeg")


def png(img: Image.Image) -> str:
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
    q = lambda im: im.quantize(colors=96, method=Image.Quantize.FASTOCTREE)
    return png(q(logo)), png(q(Image.fromarray(white.astype("uint8"))))


def photo(name):
    img = Image.open(BUILD / "photos" / f"{name}.jpg")
    return jpeg(resize(img, PHOTO_WIDTHS.get(name, 900)))


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
    for slug, name in CLIENTS:
        img = Image.open(BUILD / "clients" / f"{slug}.png").convert("RGBA")
        img = img.resize((round(img.width * 110 / img.height), 110), Image.LANCZOS) if img.height > 110 else img
        img = Image.merge("LA", (Image.new("L", img.size, 0), img.getchannel("A")))  # colour comes from CSS
        alt = "" if repeat else name
        hidden = ' aria-hidden="true"' if repeat else ""
        out.append(f'<li{hidden}><img src="{png(img)}" alt="{alt}" width="{img.width}" height="{img.height}" loading="lazy"></li>')
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


def portrait(path, w=560):
    """Crop a portrait to 4:5 (keeping the head near the top) and encode it."""
    img = Image.open(ROOT / path).convert("RGB")
    target = img.width * 5 / 4
    if img.height > target:
        top = int((img.height - target) * 0.15)
        img = img.crop((0, top, img.width, top + int(target)))
    return jpeg(resize(img, w), 78)


def team_html():
    out = []
    for i, (path, name, role) in enumerate(TEAM):
        role_html = (f'<span class="member__role">{role}</span>' if role
                     else '<span class="member__role member__role--pending">Cargo por confirmar</span>')
        lead = " member--lead" if i == 0 else ""
        out.append(
            f'<li class="member{lead}" data-reveal style="--d:{(i % 4) * 80}">'
            f'<div class="member__photo"><img src="{portrait(path)}" alt="{name}, C&amp;K Ingenieros" '
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
]


def build_page(tpl, out, path, nav, cta, title, desc, shared):
    html = (BUILD / f"{tpl}.template.html").read_text(encoding="utf-8")
    if "{{FORM}}" in html:
        html = html.replace("{{FORM}}", shared["FORM"]).replace("{{FORM_PRIVACY}}", FORM_PRIVACY.get(nav, FORM_PRIVACY["default"]))
    for key in ("HEAD", "HEADER", "FOOTER"):
        html = html.replace("{{%s}}" % key, shared[key])
    html = html.replace("{{CSS}}", shared["CSS"]).replace("{{SCRIPT}}", shared["SCRIPT"])
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
    dest = ROOT / out
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({dest.stat().st_size / 1024:.0f} KB)")


def main():
    logo, logo_white = logos()
    shared = {
        "HEAD": (PARTIALS / "head.html").read_text(encoding="utf-8"),
        "HEADER": (PARTIALS / "header.html").read_text(encoding="utf-8"),
        "FOOTER": (PARTIALS / "footer.html").read_text(encoding="utf-8"),
        "FORM": (PARTIALS / "form.html").read_text(encoding="utf-8"),
        "CSS": (PARTIALS / "style.css").read_text(encoding="utf-8"),
        "SCRIPT": (PARTIALS / "script.js").read_text(encoding="utf-8"),
        "LOGO": logo, "LOGO_WHITE": logo_white,
        "KAREN": jpeg(resize(Image.open(ROOT / "Fotografia Karen Rodriìguez.jpg"), 680), 80),
    }
    for page in PAGES:
        if (BUILD / f"{page[0]}.template.html").exists():
            build_page(*page, shared)


if __name__ == "__main__":
    main()
