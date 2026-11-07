"""Dónde va cada firma en la página y cómo evitar tapar contenido (PyMuPDF)."""
try:
    import pymupdf as fitz  # PyMuPDF (nombre nuevo)
except ImportError:
    import fitz  # PyMuPDF (nombre antiguo)

from .archivos import ruta_larga
from .i18n import en_todos, t

COLORES = {1: "#d62828", 2: "#1d4ed8"}
# Posiciones por defecto (fracciones de la página, origen arriba-izquierda)
DEFECTO = {1: (0.07, 0.86, 0.48, 0.95), 2: (0.52, 0.86, 0.93, 0.95)}


def indice_pagina(total, modo, numero):
    if modo == "primera":
        return 0
    if modo == "ultima":
        return total - 1
    return min(max(numero, 1), total) - 1


def _marcas_de_sello():
    """Inicios del texto de nuestras firmas en todos los idiomas (para no contarlas como contenido)."""
    return [m for v in en_todos("sello.marcas") for m in v.split("|")]


class SinEspacio(Exception):
    """No hay ningún lugar libre del tamaño de las firmas en la página."""


def contenido_ocupado(page):
    """Rectángulos (en coordenadas de la vista) con texto (línea por línea), imágenes o firmas previas.
    Las líneas y gráficos dibujados NO cuentan: se puede firmar sobre ellos."""
    area = page.rect.get_area()
    rot = page.rotation_matrix  # el texto viene sin rotar; la vista previa sí está rotada
    ocup = []

    def agregar(rect):
        r = fitz.Rect(rect) * rot
        r.normalize()
        ocup.append(r)

    for blk in page.get_text("dict")["blocks"]:
        if blk["type"] == 0:
            for ln in blk["lines"]:
                texto = "".join(sp["text"] for sp in ln["spans"])
                if not texto.strip() or any(m in texto for m in _marcas_de_sello()):
                    continue
                agregar(ln["bbox"])
        elif blk["type"] == 1 and fitz.Rect(blk["bbox"]).get_area() < 0.6 * area:
            agregar(blk["bbox"])  # ignora fondos o escaneos de página completa
    try:
        for w in page.widgets() or []:  # firmas ya existentes
            agregar(w.rect)
    except Exception:
        pass
    return ocup


def ubicar_cajas(page, cajas_vista, paso=6, margen=3, borde=12):
    """Busca el lugar libre más cercano moviendo todas las firmas juntas, primero hacia arriba.
    Devuelve (cajas, dy) con dy en puntos (positivo = subió, negativo = bajó)."""
    ocup = contenido_ocupado(page)
    alto = page.rect.height

    def libre(dy):
        for r in cajas_vista.values():
            t = fitz.Rect(r.x0, r.y0 - dy, r.x1, r.y1 - dy)
            if dy and (t.y0 < borde or t.y1 > alto - borde):
                return False
            c = fitz.Rect(t.x0 - margen, t.y0 - margen, t.x1 + margen, t.y1 + margen)
            if any(c.intersects(o) for o in ocup):
                return False
        return True

    for k in range(0, int(alto // paso) + 1):
        for dy in ((0,) if k == 0 else (k * paso, -k * paso)):
            if libre(dy):
                return {n: fitz.Rect(r.x0, r.y0 - dy, r.x1, r.y1 - dy) for n, r in cajas_vista.items()}, dy
    raise SinEspacio("")


def cajas_para_pdf(ruta, modo, numero, fracciones, evitar=False):
    """Convierte las fracciones de la vista previa a coordenadas PDF para ESTE documento
    (cada PDF puede tener otro tamaño de hoja). Si 'evitar', mueve las firmas a un lugar libre.
    Devuelve (indice_pagina, cajas_pdf, ajuste_en_puntos)."""
    with open(ruta_larga(ruta), "rb") as f:
        doc = fitz.open(stream=f.read(), filetype="pdf")
    try:
        idx = indice_pagina(doc.page_count, modo, numero)
        page = doc[idx]
        vw, vh = page.rect.width, page.rect.height
        rot = page.rotation
        alto_real = vw if rot in (90, 270) else vh
        vista = {n: fitz.Rect(a * vw, b * vh, c * vw, d * vh) for n, (a, b, c, d) in fracciones.items()}
        ajuste = 0
        if evitar:
            try:
                vista, ajuste = ubicar_cajas(page, vista)
            except SinEspacio:
                raise SinEspacio(t("error.sin_espacio", n=idx + 1)) from None
        cajas = {}
        for n, rv in vista.items():
            r = fitz.Rect(rv) * page.derotation_matrix
            r.normalize()
            cajas[n] = (r.x0, alto_real - r.y1, r.x1, alto_real - r.y0)
        return idx, cajas, ajuste
    finally:
        doc.close()
