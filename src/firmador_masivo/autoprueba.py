"""Autoprueba para comprobar que el programa compilado (.exe) funciona.

Se ejecuta con `FirmadorPDF.exe --autoprueba`: genera un certificado y un PDF temporales, firma,
lee el resultado y termina con código 0 si todo salió bien (1 si algo falló). No muestra ventanas
ni toca archivos del usuario."""
import datetime
import os
import tempfile


def autoprueba():
    try:
        import tkinter  # noqa: F401  (comprueba que Tk viene incluido)
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives.serialization import BestAvailableEncryption, pkcs12
        from cryptography.x509.oid import NameOID

        from .firmas import cargar_firmante, firmar_un_pdf
        from .i18n import IDIOMAS, claves, t
        from .posicion import cajas_para_pdf, fitz

        carpeta = tempfile.mkdtemp(prefix="firmador_auto_")
        llave = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        nombre = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Prueba")])
        cert = (x509.CertificateBuilder().subject_name(nombre).issuer_name(nombre)
                .public_key(llave.public_key()).serial_number(1)
                .not_valid_before(datetime.datetime(2020, 1, 1))
                .not_valid_after(datetime.datetime(2099, 1, 1)).sign(llave, hashes.SHA256()))
        p12 = os.path.join(carpeta, "a.p12")
        with open(p12, "wb") as f:
            f.write(pkcs12.serialize_key_and_certificates(b"a", llave, cert, None, BestAvailableEncryption(b"x")))
        doc = fitz.open()
        doc.new_page().insert_text((60, 70), "Hola")
        pdf = os.path.join(carpeta, "a.pdf")
        doc.save(pdf)
        firmante = cargar_firmante(p12, "x")
        idx, cajas, _ = cajas_para_pdf(pdf, "ultima", 1, {1: (0.07, 0.86, 0.48, 0.95)}, True)
        salida = os.path.join(carpeta, "f.pdf")
        firmar_un_pdf(pdf, salida, [(firmante, "Firma1", cajas[1])], idx, True, None, True)
        pagina = fitz.open(salida)[0]
        pagina.get_pixmap().tobytes("png")
        assert "Firmado electr" in pagina.get_text()
        assert all(claves(c) for c in IDIOMAS) and t("ui.firmar")
        from .validacion import verificar_pdf
        resultado = verificar_pdf(salida)
        assert resultado["error"] is None and resultado["firmas"][0]["integridad"]
        return 0
    except Exception:
        return 1
