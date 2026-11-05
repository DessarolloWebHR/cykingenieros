"""Build the standalone homepage (index.html) from home.template.html.

Optimizes the repository images and inlines them as base64 data URIs so the
output is a single self-contained HTML file.

Usage:  python3 _build/build_home.py
"""
import base64
import io
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "_build" / "home.template.html"
OUT = ROOT / "index.html"


def data_uri(img: Image.Image, fmt: str, **save_kw) -> str:
    buf = io.BytesIO()
    img.save(buf, fmt, **save_kw)
    mime = "image/png" if fmt == "PNG" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(buf.getvalue()).decode()


def logos():
    logo = Image.open(ROOT / "Transparente.png").convert("RGBA")
    logo = logo.crop(logo.getbbox())
    w = 640
    logo = logo.resize((w, round(logo.height * w / logo.width)), Image.LANCZOS)

    # White version for dark backgrounds: indigo strokes/wordmark -> white,
    # orange/yellow brand colors kept as-is.
    a = np.array(logo).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    indigo = (b > r + 20) & (b > g)
    white = a.copy()
    white[indigo, 0:3] = 255
    logo_white = Image.fromarray(white.astype("uint8"))

    q = lambda im: im.quantize(colors=96, method=Image.Quantize.FASTOCTREE)
    return data_uri(q(logo), "PNG", optimize=True), data_uri(q(logo_white), "PNG", optimize=True)


def karen():
    img = Image.open(ROOT / "Fotografia Karen Rodriìguez.jpg").convert("RGB")
    w = 680
    img = img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)
    return data_uri(img, "JPEG", quality=80, optimize=True, progressive=True)


# Placeholder logo slots — clearly marked until C&K approves real client logos.
MARKS = [
    '<circle cx="15" cy="15" r="11"/><path d="M9 15h12"/>',
    '<rect x="4" y="4" width="22" height="22"/><path d="M4 26 26 4"/>',
    '<path d="M15 3 27 26H3Z"/>',
    '<circle cx="11" cy="15" r="7"/><circle cx="19" cy="15" r="7"/>',
    '<path d="M4 22V8l11 8 11-8v14"/>',
    '<rect x="4" y="9" width="22" height="12" rx="6"/>',
    '<path d="M15 3v24M3 15h24"/><circle cx="15" cy="15" r="7"/>',
    '<path d="M4 20c4-10 8-10 11 0s7 10 11 0"/>',
]


def logo_slots():
    out = []
    for i, m in enumerate(MARKS, 1):
        out.append(
            f'<li class="logo-slot"><svg viewBox="0 0 30 30" fill="none" stroke="currentColor" '
            f'stroke-width="1.6" aria-hidden="true">{m}</svg>'
            f"<span><b>Cliente {i:02d}</b><small>Logo pendiente</small></span></li>"
        )
    return "\n        ".join(out)


def main():
    logo, logo_white = logos()
    html = TEMPLATE.read_text(encoding="utf-8")
    html = (
        html.replace("{{LOGO_WHITE}}", logo_white)
        .replace("{{LOGO_SLOTS}}", logo_slots())
        .replace("{{LOGO}}", logo)
        .replace("{{KAREN}}", karen())
    )
    OUT.write_text(html, encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)} ({OUT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
