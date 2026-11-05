"""Combine the built pages into one navigable preview page for claude.ai artifacts.

Each artifact is a single page, so root links such as /nosotros/ can't resolve there.
This joins every built page into one document and switches between them with
#hash routing. Links to pages not built yet show a short "en desarrollo" notice.
Production files (index.html, nosotros/index.html, ...) are not changed.

Usage:  python3 _build/preview.py OUTPUT.html
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = [("inicio", "index.html", "/"), ("nosotros", "nosotros/index.html", "/nosotros/")]
PENDING = ["servicios", "proyectos", "contacto", "politica-de-privacidad"]


def part(html, start, end, inner=True):
    i = html.index(start)
    j = html.index(end, i)
    return html[i + len(start):j] if inner else html[i:j]


def main(out):
    built = {key: (ROOT / f).read_text(encoding="utf-8") for key, f, _ in PAGES}
    home = built["inicio"]
    head = part(home, "<head>", "</head>")
    head = re.sub(r"<meta charset[^>]*>\s*|<meta name=\"viewport\"[^>]*>\s*", "", head)
    head = re.sub(r"<title>.*?</title>\s*", "", head, flags=re.S)
    head = re.sub(r"<style>.*?</style>", "", head, flags=re.S)
    styles = "".join(re.findall(r"<style>(.*?)</style>", built["nosotros"], flags=re.S))  # shared + page CSS
    header = part(home, "<body>", '<main id="main">')
    footer = part(home, "</main>", "<script>")
    script = part(home, "<script>\n(function(){", "</script>", inner=False) + "</script>"
    mains = "".join(
        f'<div class="pv-page" data-page="{key}"{"" if key == "inicio" else " hidden"}>'
        + part(html, '<main id="main">', "</main>") + "</div>"
        for key, html in built.items()
    )
    pending = ('<div class="pv-page pv-pending" data-page="pendiente" hidden><div class="container">'
               '<p class="eyebrow">Vista previa</p><h1 class="h2">Esta página está en desarrollo.</h1>'
               '<p class="lead">Servicios, Proyectos y Contacto se diseñarán a continuación con el mismo estilo.</p>'
               '<a class="btn btn--navy" href="#inicio">Volver al inicio<span class="btn__ico" aria-hidden="true">→</span></a>'
               '</div></div>')
    body = header.replace("<a class=\"skip\" href=\"#main\">", "<a class=\"skip\" href=\"#main\">") \
        + '<main id="main">' + mains + pending + "</main>" + footer + script
    body = header + '<main id="main">' + mains + pending + "</main>" + footer + script

    def link(m):
        path, frag = m.group(1), m.group(2) or ""
        for key, _, url in PAGES:
            if path == url:
                return f'href="#{frag[1:] if frag else key}"'
        slug = path.strip("/").split("/")[0]
        if slug in PENDING:
            return 'href="#pendiente"'
        return m.group(0)
    body = re.sub(r'href="(/[^"#]*)(#[^"]*)?"', link, body)
    # current-page marker is set by the router instead of the static build
    body = body.replace(' aria-current="page"', "")

    router = """<script>
(function(){
  var pages=[].slice.call(document.querySelectorAll('.pv-page'));
  var nav=[].slice.call(document.querySelectorAll('.nav a, .mnav nav a'));
  function show(name){
    pages.forEach(function(p){p.hidden=p.getAttribute('data-page')!==name;});
    nav.forEach(function(a){if(a.getAttribute('href')==='#'+name)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
    var cta=document.querySelector('.header__cta');
    if(cta)cta.setAttribute('href',name==='inicio'?'#contacto':'#pendiente');
  }
  function route(){
    var h=decodeURIComponent(location.hash.slice(1))||'inicio';
    var page=pages.filter(function(p){return p.getAttribute('data-page')===h;})[0];
    if(page){show(h);window.scrollTo(0,0);return;}
    var el=document.getElementById(h);
    if(!el)return;
    var owner=el.closest('.pv-page');
    if(owner&&owner.hidden){show(owner.getAttribute('data-page'));}
    requestAnimationFrame(function(){el.scrollIntoView();});
  }
  window.addEventListener('hashchange',route);
  route();
})();
</script>"""
    css = ".pv-pending{padding-block:clamp(120px,16vw,200px);text-align:center}.pv-pending .container{display:grid;justify-items:center;gap:20px}"
    page = ("<title>C&amp;K Ingenieros</title>\n" + head + "<style>" + styles + css + "</style>\n" + body + router)
    Path(out).write_text(page, encoding="utf-8")
    print(f"wrote {out} ({Path(out).stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main(sys.argv[1])
