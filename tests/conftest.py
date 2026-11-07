"""Utilidades de prueba. Todo se genera al vuelo: no hay certificados ni PDFs en el repo."""
import datetime
import os
import tempfile

# El idioma elegido se guarda en un archivo de configuración: las pruebas usan una carpeta temporal
os.environ["FIRMADOR_CONFIG_DIR"] = tempfile.mkdtemp(prefix="firmador_cfg_")

import pymupdf
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import BestAvailableEncryption, pkcs12
from cryptography.x509.oid import NameOID

CLAVE = "clave-de-prueba"

LETTER = (612, 792)
A4 = (595, 842)


def crear_p12(ruta, nombre, desde, hasta, clave=CLAVE):
    """Genera un .p12 autofirmado de prueba."""
    k = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    n = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, nombre)])
    c = (x509.CertificateBuilder().subject_name(n).issuer_name(n).public_key(k.public_key())
         .serial_number(x509.random_serial_number())
         .not_valid_before(desde).not_valid_after(hasta)
         .add_extension(x509.KeyUsage(True, True, False, False, False, False, False, False, False), True)
         .sign(k, hashes.SHA256()))
    ruta.write_bytes(pkcs12.serialize_key_and_certificates(
        nombre.encode("utf-8"), k, c, None, BestAvailableEncryption(clave.encode("utf-8"))))
    return str(ruta)


def crear_pdf(ruta, tam=LETTER, textos=(), rect_azul=None, rotacion=0, paginas=1):
    """PDF de prueba. textos: lista de (x, y_desde_abajo, texto, tamaño_fuente)."""
    ruta = type(ruta)(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open()
    for _ in range(paginas):
        page = doc.new_page(width=tam[0], height=tam[1])
        page.insert_text((60, 70), "Documento de prueba", fontsize=11)
        page.insert_text((60, 90), "Detalle contable", fontsize=11)
        for x, y, texto, fs in textos:
            page.insert_text((x, tam[1] - y), texto, fontsize=fs)
        if rect_azul:
            x0, y0, x1, y1 = rect_azul  # coordenadas de vista (origen arriba-izquierda)
            page.draw_rect(pymupdf.Rect(x0, y0, x1, y1), color=(0.2, 0.4, 0.8), fill=(0.2, 0.4, 0.8))
    if rotacion:
        doc[0].set_rotation(rotacion)
    doc.save(str(ruta))
    doc.close()
    return str(ruta)


PIE_IZQ = [(45, 40, "Elaboró: Persona de Prueba", 8), (45, 28, "Id Doc: 000000", 8)]
PIE_ANCHO = [(40, y, "Texto de pie de página largo " * 6, 8) for y in range(20, 150, 10)]
LLENO = lambda alto: [(30, y, "Línea de texto que ocupa todo el ancho de la hoja " * 3, 9)  # noqa: E731
                      for y in range(15, int(alto) - 15, 11)]


@pytest.fixture(scope="session")
def certs(tmp_path_factory):
    d = tmp_path_factory.mktemp("certs")
    ini = datetime.datetime(2020, 1, 1)
    fin = datetime.datetime(2099, 1, 1)
    ahora = datetime.datetime.now()
    return {
        "uno": crear_p12(d / "uno.p12", "Firmante Uno", ini, fin),
        "dos": crear_p12(d / "dos.p12", "Firmante Dos", ini, fin),
        "tilde": crear_p12(d / "tilde.p12", "José Muñoz Peña", ini, fin),
        "vencida": crear_p12(d / "vencida.p12", "Vencida SA", ahora - datetime.timedelta(days=900),
                             ahora - datetime.timedelta(days=10)),
        "por_vencer": crear_p12(d / "por_vencer.p12", "Por Vencer", ahora - datetime.timedelta(days=300),
                                ahora + datetime.timedelta(days=12)),
        "futura": crear_p12(d / "futura.p12", "Futura SA", ahora + datetime.timedelta(days=30),
                            ahora + datetime.timedelta(days=400)),
    }


@pytest.fixture
def firmantes(certs):
    from firmador_masivo.firmas import cargar_firmante
    return cargar_firmante(certs["uno"], CLAVE), cargar_firmante(certs["dos"], CLAVE)


@pytest.fixture
def pdf_simple(tmp_path):
    return crear_pdf(tmp_path / "simple.pdf", paginas=2)


def firmas_de(ruta):
    """Devuelve [(nombre_campo, intacta)] de las firmas incrustadas."""
    from pyhanko.pdf_utils.reader import PdfFileReader
    from pyhanko.sign.validation import validate_pdf_signature
    with open(ruta, "rb") as f:
        r = PdfFileReader(f)
        return [(s.field_name, validate_pdf_signature(s).intact) for s in r.embedded_signatures]


@pytest.fixture(autouse=True)
def idioma_espanol():
    """Cada prueba parte en español; las que cambian de idioma lo restauran."""
    from firmador_masivo import i18n
    i18n.fijar_idioma("es")
    yield
    i18n.fijar_idioma("es")
