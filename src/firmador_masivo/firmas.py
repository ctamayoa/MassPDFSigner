"""Certificados, sello de tiempo y firmado de un PDF (pyHanko)."""
import datetime
import io
import os

from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter
from pyhanko.sign import signers
from pyhanko.sign.fields import SigFieldSpec
from pyhanko.stamp import QRPosition, QRStampStyle, TextStampStyle

from .archivos import ruta_larga
from .errores import log


def cargar_firmante(ruta_p12, clave):
    # pyHanko devuelve None (sin error) si la contraseña es incorrecta
    firmante = signers.SimpleSigner.load_pkcs12(
        pfx_file=ruta_p12, passphrase=clave.encode("utf-8")
    )
    if firmante is None:
        raise ValueError("Contraseña incorrecta o archivo .p12 dañado")
    return firmante


def crear_sellador(url, usuario="", clave=""):
    """Cliente de sello de tiempo (RFC 3161)."""
    from pyhanko.sign.timestamps import HTTPTimeStamper
    auth = (usuario, clave) if usuario else None
    return HTTPTimeStamper(url.strip(), https=False, timeout=20, auth=auth)


def probar_sellador(url, usuario="", clave=""):
    """Pide un sello de prueba al servidor. Devuelve (ok, texto)."""
    import asyncio
    import hashlib
    if not url.strip().lower().startswith(("http://", "https://")):
        return False, "La dirección debe empezar con http:// o https://"
    try:
        sellador = crear_sellador(url, usuario, clave)
        asyncio.run(sellador.async_timestamp(hashlib.sha256(b"prueba").digest(), "sha256"))
        return True, "El servidor respondió con un sello de tiempo válido."
    except Exception as e:
        log.debug("Falló la prueba del servidor de sello de tiempo", exc_info=e)
        return False, ("No se pudo obtener el sello de tiempo.\n\n"
                       "Revisa la dirección del servidor, el usuario y la clave (si los pide) "
                       "y tu conexión a internet.")


def nombre_titular(cert):
    return cert.subject.native.get("common_name") or cert.subject.human_friendly


def texto_qr(firmante):
    """Texto del QR: resumen de la firma (firmante y fecha)."""
    nombre = nombre_titular(firmante.signing_cert)
    fecha = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    return (
        f"FIRMADO POR: {nombre}\n"
        "RAZON: \n"
        "LOCALIZACION: \n"
        f"FECHA: {fecha}\n"
        "Firmado digitalmente con Firmador Masivo PDF"
    )


def revisar_firma(ruta_p12, clave):
    """Devuelve (ok, texto). Abre el .p12 con la clave y lee titular y vigencia."""
    if not ruta_p12:
        return False, "No has seleccionado el archivo .p12."
    if not os.path.isfile(ruta_p12):
        return False, "No se encuentra el archivo seleccionado."
    if not clave:
        return False, "Falta la contraseña."
    try:
        firmante = cargar_firmante(ruta_p12, clave)
    except Exception:
        return False, "Contraseña incorrecta o archivo .p12 dañado."
    cert = firmante.signing_cert
    nombre = nombre_titular(cert)
    validez = cert["tbs_certificate"]["validity"]
    desde = validez["not_before"].native
    hasta = validez["not_after"].native
    ahora = datetime.datetime.now(datetime.timezone.utc)
    if hasta < ahora:
        return False, f"{nombre}\nVENCIDA el {hasta:%d/%m/%Y}. Las firmas saldrían inválidas."
    if desde > ahora:
        return False, f"{nombre}\nAún no es válida (empieza el {desde:%d/%m/%Y})."
    dias = (hasta - ahora).days
    aviso = f"  (vence en {dias} días)" if dias <= 30 else ""
    return True, f"{nombre}\nVálida hasta el {hasta:%d/%m/%Y}{aviso}"


def firmar_un_pdf(ruta_entrada, ruta_salida, firmantes, pagina, visible, tsa=None, qr=False):
    """firmantes: lista de (SimpleSigner, nombre_campo, caja_pdf)."""
    with open(ruta_larga(ruta_entrada), "rb") as f:
        datos = io.BytesIO(f.read())

    for firmante, campo, caja in firmantes:
        escritor = IncrementalPdfFileWriter(datos, strict=False)
        spec = SigFieldSpec(
            sig_field_name=campo,
            on_page=pagina,
            box=tuple(round(v, 2) for v in caja) if visible else None,
        )
        estilo = None
        parametros = None
        if visible and qr:
            # Recuadro con QR a la izquierda y texto a la derecha
            estilo = QRStampStyle(
                stamp_text="Firmado electrónicamente por:\n%(signer)s",
                border_width=1,
                qr_position=QRPosition.LEFT_OF_TEXT,
            )
            parametros = {"url": texto_qr(firmante)}
        elif visible:
            estilo = TextStampStyle(
                stamp_text="Firmado electrónicamente por:\n%(signer)s\nFecha: %(ts)s",
                border_width=1,
            )
        meta = signers.PdfSignatureMetadata(field_name=campo)
        sellador = (tsa if hasattr(tsa, "async_timestamp") else crear_sellador(*tsa)) if tsa else None
        pdf_signer = signers.PdfSigner(
            meta, signer=firmante, new_field_spec=spec, stamp_style=estilo,
            timestamper=sellador,
        )
        salida = io.BytesIO()
        pdf_signer.sign_pdf(escritor, output=salida, appearance_text_params=parametros)
        salida.seek(0)
        datos = salida

    with open(ruta_larga(ruta_salida), "wb") as f:
        f.write(datos.getvalue())
