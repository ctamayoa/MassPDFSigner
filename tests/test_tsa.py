"""Sello de tiempo contra un servidor TSA local de prueba (RFC 3161)."""
import datetime
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from asn1crypto import keys as akeys
from asn1crypto import tsp
from asn1crypto import x509 as ax509
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.timestamps import DummyTimeStamper
from pyhanko.sign.validation import validate_pdf_signature

from firmador_masivo.firmas import crear_sellador, firmar_un_pdf, probar_sellador

CAJAS = [(40, 40, 285, 115)]


@pytest.fixture(scope="module")
def servidor_tsa():
    k = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    n = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "TSA de Prueba")])
    c = (x509.CertificateBuilder().subject_name(n).issuer_name(n).public_key(k.public_key())
         .serial_number(x509.random_serial_number())
         .not_valid_before(datetime.datetime(2020, 1, 1)).not_valid_after(datetime.datetime(2099, 1, 1))
         .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.TIME_STAMPING]), True)
         .sign(k, hashes.SHA256()))
    cert = ax509.Certificate.load(c.public_bytes(serialization.Encoding.DER))
    llave = akeys.PrivateKeyInfo.load(k.private_bytes(
        serialization.Encoding.DER, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    dummy = DummyTimeStamper(cert, llave)
    consultas = {"n": 0}

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            datos = self.rfile.read(int(self.headers["Content-Length"]))
            consultas["n"] += 1
            out = dummy.request_tsa_response(tsp.TimeStampReq.load(datos)).dump()
            self.send_response(200)
            self.send_header("Content-Type", "application/timestamp-reply")
            self.send_header("Content-Length", str(len(out)))
            self.end_headers()
            self.wfile.write(out)

        def log_message(self, *a):
            pass

    srv = HTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}/tsa", consultas
    srv.shutdown()


def test_probar_sellador_ok(servidor_tsa):
    ok, texto = probar_sellador(servidor_tsa[0])
    assert ok and "válido" in texto


def test_probar_sellador_url_mala():
    ok, texto = probar_sellador("ftp://x")
    assert not ok and "http://" in texto


def test_probar_sellador_servidor_caido_no_filtra_detalle_tecnico():
    ok, texto = probar_sellador("http://127.0.0.1:9/tsa")
    assert not ok
    assert "Traceback" not in texto and "Errno" not in texto and "127.0.0.1" not in texto


def test_sellos_validos_y_un_solo_cliente(tmp_path, pdf_simple, firmantes, servidor_tsa):
    url, consultas = servidor_tsa
    s1, s2 = firmantes
    sellador = crear_sellador(url)          # un solo cliente para toda la corrida
    firmantes_pdf = [(s1, "Firma1", CAJAS[0]), (s2, "Firma2", (310, 40, 555, 115))]
    salida = str(tmp_path / "con_sello.pdf")
    firmar_un_pdf(pdf_simple, salida, firmantes_pdf, -1, True, sellador)
    tras_primero = consultas["n"]
    firmar_un_pdf(pdf_simple, str(tmp_path / "otro.pdf"), firmantes_pdf, -1, True, sellador)
    # el segundo PDF solo pide un sello por firma: no repite la consulta de medición
    assert consultas["n"] - tras_primero == 2
    with open(salida, "rb") as f:
        for s in PdfFileReader(f).embedded_signatures:
            st = validate_pdf_signature(s)
            assert st.intact
            assert st.timestamp_validity is not None and st.timestamp_validity.intact


def test_tsa_como_tupla(tmp_path, pdf_simple, firmantes, servidor_tsa):
    salida = str(tmp_path / "tupla.pdf")
    firmar_un_pdf(pdf_simple, salida, [(firmantes[0], "Firma1", CAJAS[0])], -1, True, (servidor_tsa[0], "", ""))
    with open(salida, "rb") as f:
        st = validate_pdf_signature(PdfFileReader(f).embedded_signatures[0])
    assert st.timestamp_validity is not None
