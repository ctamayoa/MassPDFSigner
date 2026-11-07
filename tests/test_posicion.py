import pymupdf
import pytest

from conftest import A4, LETTER, LLENO, PIE_ANCHO, PIE_IZQ, crear_pdf
from firmador_masivo.posicion import SinEspacio, cajas_para_pdf, indice_pagina

FRAC = {1: (0.07, 0.88, 0.48, 0.96), 2: (0.52, 0.88, 0.93, 0.96)}


@pytest.mark.parametrize("modo,numero,total,esperado", [
    ("primera", 1, 5, 0), ("ultima", 1, 5, 4), ("numero", 3, 5, 2),
    ("numero", 99, 5, 4), ("numero", 0, 5, 0),
])
def test_indice_pagina(modo, numero, total, esperado):
    assert indice_pagina(total, modo, numero) == esperado


def _vista(caja_pdf, pagina):
    """Convierte una caja PDF (origen abajo-izq.) a coordenadas de vista para comparar."""
    x0, y0, x1, y1 = caja_pdf
    r = pymupdf.Rect(x0, pagina.mediabox.height - y1, x1, pagina.mediabox.height - y0)
    r = r * pagina.rotation_matrix
    r.normalize()
    return r


def _choca(ruta, caja_pdf, pagina_idx=-1):
    """¿La caja pisa algún texto de la página original?"""
    doc = pymupdf.open(ruta)
    pg = doc[pagina_idx]
    caja = _vista(caja_pdf, pg)
    for b in pg.get_text("dict")["blocks"]:
        if b["type"] != 0:
            continue
        for ln in b["lines"]:
            r = pymupdf.Rect(ln["bbox"]) * pg.rotation_matrix
            r.normalize()
            if r.intersects(caja):
                return True
    return False


def test_documento_libre_no_se_mueve(tmp_path):
    ruta = crear_pdf(tmp_path / "libre.pdf")
    idx, cajas, ajuste = cajas_para_pdf(ruta, "ultima", 1, FRAC, evitar=True)
    assert idx == 0 and ajuste == 0 and set(cajas) == {1, 2}


def test_sin_evitar_no_mueve_aunque_choque(tmp_path):
    ruta = crear_pdf(tmp_path / "pie.pdf", textos=PIE_IZQ)
    _, _, ajuste = cajas_para_pdf(ruta, "ultima", 1, FRAC, evitar=False)
    assert ajuste == 0


@pytest.mark.parametrize("nombre,tam,textos,rotacion", [
    ("pie_izq", LETTER, PIE_IZQ, 0),
    ("pie_ancho", A4, PIE_ANCHO, 0),
    ("horizontal", (792, 612), PIE_IZQ, 0),
    ("rotado", LETTER, [(560, y, "Pie lateral de página rotada", 8) for y in range(100, 700, 12)], 90),
])
def test_evita_tapar_texto(tmp_path, nombre, tam, textos, rotacion):
    ruta = crear_pdf(tmp_path / f"{nombre}.pdf", tam=tam, textos=textos, rotacion=rotacion)
    _, sin_mover, _ = cajas_para_pdf(ruta, "ultima", 1, FRAC, evitar=False)
    assert any(_choca(ruta, c) for c in sin_mover.values()), "el caso de prueba debe chocar sin ajuste"
    _, cajas, ajuste = cajas_para_pdf(ruta, "ultima", 1, FRAC, evitar=True)
    assert ajuste != 0, "debía moverse para no tapar el pie"
    assert not any(_choca(ruta, c) for c in cajas.values())


def test_imagen_o_rectangulo_cuenta_como_obstaculo(tmp_path):
    # Una imagen real bajo la caja: se inserta un PNG pequeño.
    ruta = tmp_path / "img.pdf"
    doc = pymupdf.open()
    pg = doc.new_page(width=612, height=792)
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 40, 20))
    pix.set_rect(pix.irect, (30, 90, 200))
    pg.insert_image(pymupdf.Rect(60, 700, 260, 750), pixmap=pix)
    doc.save(str(ruta))
    _, _, ajuste = cajas_para_pdf(str(ruta), "ultima", 1, FRAC, evitar=True)
    assert ajuste != 0


def test_graficos_no_son_obstaculo(tmp_path):
    ruta = crear_pdf(tmp_path / "grafico.pdf", rect_azul=(60, 700, 260, 750))
    _, _, ajuste = cajas_para_pdf(ruta, "ultima", 1, FRAC, evitar=True)
    assert ajuste == 0


def test_sin_espacio_lanza_con_mensaje_en_espanol(tmp_path):
    ruta = crear_pdf(tmp_path / "lleno.pdf", textos=LLENO(792))
    with pytest.raises(SinEspacio) as e:
        cajas_para_pdf(ruta, "ultima", 1, FRAC, evitar=True)
    assert str(e.value) == "No hay espacio libre para las firmas en la página 1"


def test_pagina_elegida(tmp_path):
    ruta = crear_pdf(tmp_path / "tres.pdf", paginas=3)
    assert cajas_para_pdf(ruta, "primera", 1, FRAC)[0] == 0
    assert cajas_para_pdf(ruta, "ultima", 1, FRAC)[0] == 2
    assert cajas_para_pdf(ruta, "numero", 2, FRAC)[0] == 1


def test_cada_pdf_usa_su_tamano(tmp_path):
    a = cajas_para_pdf(crear_pdf(tmp_path / "a.pdf", tam=A4), "ultima", 1, {1: FRAC[1]})[1][1]
    b = cajas_para_pdf(crear_pdf(tmp_path / "b.pdf", tam=LETTER), "ultima", 1, {1: FRAC[1]})[1][1]
    assert a != b
    assert a[2] == pytest.approx(A4[0] * FRAC[1][2], abs=0.01)


def test_pdf_danado_falla_y_se_traduce(tmp_path):
    from firmador_masivo.errores import describir_error
    from firmador_masivo.i18n import t
    mal = tmp_path / "malo.pdf"
    mal.write_bytes(b"esto no es un pdf")
    with pytest.raises(Exception) as e:
        cajas_para_pdf(str(mal), "ultima", 1, FRAC)
    assert describir_error(e.value) == t("error.danado")
