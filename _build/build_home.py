"""Build the standalone homepage (index.html) from home.template.html.

Optimizes the repository images and the photos in _build/photos/ and inlines
them as base64 data URIs, so the output is a single self-contained HTML file.

Photos in _build/photos/ are free-licence Unsplash images used as references
until C&K supplies its own project photography.

Usage:  python3 _build/build_home.py
"""
import base64
import io
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
TEMPLATE = BUILD / "home.template.html"
OUT = ROOT / "index.html"

ARROW = ('<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8" '
         'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 8h10M9 4l4 4-4 4"/></svg>')

# name -> output width
PHOTO_WIDTHS = {"hero": 2000, "approach": 1200, "svc-tarifaria": 1100}

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
    ("prj-1", "Infraestructura clínica"),
    ("prj-2", "Construcción eléctrica"),
    ("prj-3", "Agro y viñedos"),
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
    white = a.copy()
    white[indigo, 0:3] = 255
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
    for i, (img, sector) in enumerate(PROJECTS):
        out.append(
            f'<li class="prj" data-reveal style="--d:{i * 90}">'
            f'<div class="prj__media"><span class="prj__badge">Proyecto por confirmar</span>'
            f'<img src="{photo(img)}" alt="Imagen referencial — {sector}" width="900" height="600" loading="lazy"></div>'
            f'<div class="prj__body"><span class="prj__sector">{sector}</span>'
            f'<h3>Nombre del proyecto</h3>'
            f'<p>Breve descripción del trabajo realizado. Espacio reservado para un proyecto real aprobado por C&amp;K.</p>'
            f'<a class="link" href="/proyectos/">Ver proyecto {ARROW}</a></div></li>'
        )
    return "\n      ".join(out)


def logo_slots():
    return "".join(
        f'<li class="logo-slot"><span>Cliente {i:02d}<small>Logo pendiente</small></span></li>' for i in range(1, 9)
    )


def main():
    logo, logo_white = logos()
    karen = jpeg(resize(Image.open(ROOT / "Fotografia Karen Rodriìguez.jpg"), 680), 80)
    html = TEMPLATE.read_text(encoding="utf-8")
    html = (html.replace("{{SERVICES}}", services_html())
                .replace("{{PROJECTS}}", projects_html())
                .replace("{{LOGO_SLOTS}}", logo_slots())
                .replace("{{LOGO_WHITE}}", logo_white)
                .replace("{{LOGO}}", logo)
                .replace("{{KAREN}}", karen)
                .replace("{{ARROW}}", ARROW))
    for name in ("hero", "approach", "svc-tarifaria", "ind-salud", "ind-industria", "ind-agro"):
        html = html.replace("{{IMG:%s}}" % name, photo(name))
    assert "{{" not in html, html[html.index("{{"):html.index("{{") + 40]
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
