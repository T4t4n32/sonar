# /// script
# requires-python = ">=3.10"
# ///
"""Busca piezas en tiendas colombianas de electrónica que se pueden leer sin sesión (Vistronica, Electronilab, Sigma).
Solo lee páginas públicas; no compra nada. Mercado Libre bloquea a los programas (muro de verificación de cuenta): se busca a mano.

    uv run --script tools/compras_buscar.py "mg996r" "esp32-cam" --max 4
"""
from __future__ import annotations
import argparse, html, re, sys, urllib.parse, urllib.request

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/130 Safari/537.36"
TIENDAS = {
    "vistronica": "https://www.vistronica.com/buscar?controller=search&s={q}",
    "electronilab": "https://electronilab.co/?s={q}&post_type=product",
    "sigma": "https://sigmaelectronica.net/?s={q}&post_type=product",
}

def leer(url: str) -> str:
    r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=25)
    return r.read().decode("utf-8", "replace")

def limpiar(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()

def productos(tienda: str, h: str, n: int) -> list[tuple[str, str, str, str]]:
    out = []
    if tienda == "vistronica":
        for m in re.finditer(r'<article[^>]*class="[^"]*product-miniature[^"]*"[^>]*>(.*?)</article>', h, re.S):
            b = m.group(1)
            t = re.search(r'product-title[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', b, re.S)
            p = re.search(r'class="price[^"]*"[^>]*>(.*?)</span>', b, re.S)
            a = "agotado" if re.search(r'(?i)agotado|out-of-stock|sin existencias', b) else ""
            if t: out.append((limpiar(t.group(2)), limpiar(p.group(1)) if p else "?", a, t.group(1)))
    else:
        for m in re.finditer(r'<li[^>]*class="[^"]*\bproduct\b[^"]*"[^>]*>(.*?)</li>', h, re.S):
            b = m.group(1)
            t = re.search(r'<a[^>]*href="([^"]+)"[^>]*class="[^"]*woocommerce-LoopProduct-link[^"]*"|<a[^>]*href="([^"]+)"', b)
            nm = re.search(r'woocommerce-loop-product__title[^>]*>(.*?)</h\d>', b, re.S)
            p = re.findall(r'woocommerce-Price-amount[^>]*>(.*?)</span>\s*</span>|woocommerce-Price-amount[^>]*>(.*?)</bdi>', b, re.S)
            pr = limpiar(" ".join(x for tup in p[:2] for x in tup if x)) if p else "?"
            a = "agotado" if re.search(r'(?i)outofstock|agotado|sin existencias', b) else ""
            if nm: out.append((limpiar(nm.group(1)), pr, a, (t.group(1) or t.group(2)) if t else ""))
    return out[:n]

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("consultas", nargs="+")
    ap.add_argument("--max", type=int, default=4)
    a = ap.parse_args()
    for q in a.consultas:
        print(f"\n=== {q}")
        for tienda, plantilla in TIENDAS.items():
            try:
                lista = productos(tienda, leer(plantilla.format(q=urllib.parse.quote_plus(q))), a.max)
            except Exception as e:
                print(f"  [{tienda}] error: {type(e).__name__}")
                continue
            if not lista:
                print(f"  [{tienda}] sin resultados")
            for nombre, precio, estado, url in lista:
                print(f"  [{tienda}] {nombre[:70]} | {precio[:24]} {estado} | {url[:90]}")

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
