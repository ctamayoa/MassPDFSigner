import pymupdf
import pytest

from conftest import CLAVE, firmas_de
from firmador_masivo.firmas import (cargar_firmante, firmar_un_pdf, revisar_firma, texto_qr)

CAJAS = [(40, 40, 285, 115), (310, 40, 555, 115)]


def test_cargar_firmante_ok(certs):
    assert cargar_firmante(certs["uno"], CLAVE) is not None


def test_cargar_firmante_clave_incorrecta(certs):
    with pytest.raises(ValueError, match="Contraseña incorrecta"):
        cargar_firmante(certs["uno"], "otra")


@pytest.mark.parametrize("caso,esperado_ok,fragmento", [
    ("uno", True, "Firmante Uno"),
    ("vencida", False, "VENCIDA"),
    ("por_vencer", True, "vence en"),
    ("futura", False, "Aún no es válida"),
])
def test_revisar_firma_vigencia(certs, caso, esperado_ok, fragmento):
    ok, texto = revisar_firma(certs[caso], CLAVE)
    assert ok is esperado_ok
    assert fragmento in texto


@pytest.mark.parametrize("ruta,clave,fragmento", [
    ("", "", "No has seleccionado"),
    ("no_existe.p12", "a", "No se encuentra"),
])
def test_revisar_firma_entradas_invalidas(ruta, clave, fragmento):
    ok, texto = revisar_firma(ruta, clave)
    assert not ok and fragmento in texto


def test_revisar_firma_sin_clave_y_clave_mala(certs):
    assert revisar_firma(certs["uno"], "") == (False, "Falta la contraseña.")
    assert revisar_firma(certs["uno"], "xxx") == (False, "Contraseña incorrecta o archivo .p12 dañado.")


def test_revisar_firma_archivo_roto(tmp_path):
    roto = tmp_path / "roto.p12"
    roto.write_bytes(b"no soy un p12")
    ok, texto = revisar_firma(str(roto), "a")
    assert not ok and "dañado" in texto


@pytest.mark.parametrize("qr", [False, True])
def test_dos_firmas_visibles_integras(tmp_path, pdf_simple, firmantes, qr):
    s1, s2 = firmantes
    salida = str(tmp_path / "firmado.pdf")
    firmar_un_pdf(pdf_simple, salida, [(s1, "Firma1", CAJAS[0]), (s2, "Firma2", CAJAS[1])], -1, True, None, qr)
    assert firmas_de(salida) == [("Firma1", True), ("Firma2", True)]
    texto = pymupdf.open(salida)[-1].get_text()
    assert "Firmado electrónicamente por" in texto
    assert "Firmante Uno" in texto and "Firmante Dos" in texto


def test_firma_invisible(tmp_path, pdf_simple, firmantes):
    s1, _ = firmantes
    salida = str(tmp_path / "invisible.pdf")
    firmar_un_pdf(pdf_simple, salida, [(s1, "Firma1", None)], 0, False)
    assert firmas_de(salida) == [("Firma1", True)]
    assert "Firmado" not in pymupdf.open(salida)[0].get_text()


def test_nombre_con_tilde_en_el_sello(tmp_path, pdf_simple, certs):
    s = cargar_firmante(certs["tilde"], CLAVE)
    for qr in (False, True):
        salida = str(tmp_path / f"tilde_{qr}.pdf")
        firmar_un_pdf(pdf_simple, salida, [(s, "Firma1", CAJAS[0])], -1, True, None, qr)
        assert "José Muñoz Peña" in pymupdf.open(salida)[-1].get_text()


def test_texto_qr_sin_referencias_a_terceros(firmantes):
    t = texto_qr(firmantes[0])
    assert "FIRMADO POR: Firmante Uno" in t
    assert t.endswith("Firmado digitalmente con Firmador Masivo PDF")
    for prohibido in ("FirmaEC", "Security Data", "Adobe"):
        assert prohibido not in t


def test_qr_legible(tmp_path, pdf_simple, firmantes):
    cv2 = pytest.importorskip("cv2")
    np = pytest.importorskip("numpy")
    s1, _ = firmantes
    salida = str(tmp_path / "qr.pdf")
    firmar_un_pdf(pdf_simple, salida, [(s1, "Firma1", CAJAS[0])], -1, True, None, True)
    pg = pymupdf.open(salida)[-1]
    pix = pg.get_pixmap(matrix=pymupdf.Matrix(4, 4), clip=pymupdf.Rect(30, pg.rect.height - 125, 300, pg.rect.height - 30))
    img = cv2.imdecode(np.frombuffer(pix.tobytes("png"), np.uint8), cv2.IMREAD_COLOR)
    ok, textos, _, _ = cv2.QRCodeDetector().detectAndDecodeMulti(img)
    assert ok and any("FIRMADO POR: Firmante Uno" in t for t in textos)
