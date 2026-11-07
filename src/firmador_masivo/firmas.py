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
from .i18n import t


def cargar_firmante(ruta_p12, clave):
    # pyHanko devuelve None (sin error) si la contraseña es incorrecta
    firmante = signers.SimpleSigner.load_pkcs12(
        pfx_file=ruta_p12, passphrase=clave.encode("utf-8")
    )
    if firmante is None:
        raise ValueError(t("rev.error_interno"))
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
        return False, t("tsa.url_invalida")
    try:
        sellador = crear_sellador(url, usuario, clave)
        asyncio.run(sellador.async_timestamp(hashlib.sha256(b"prueba").digest(), "sha256"))
        return True, t("tsa.ok")
    except Exception as e:
        log.debug("Falló la prueba del servidor de sello de tiempo", exc_info=e)
        return False, t("tsa.fallo")


def nombre_titular(cert):
    return cert.subject.native.get("common_name") or cert.subject.human_friendly


def texto_qr(firmante):
    """Texto del QR: resumen de la firma (firmante y fecha)."""
    nombre = nombre_titular(firmante.signing_cert)
    fecha = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    return "\n".join([
        t("qr.firmado_por", nombre=nombre),
        t("qr.razon"),
        t("qr.localizacion"),
        t("qr.fecha", fecha=fecha),
        t("qr.pie"),
    ])


def revisar_firma(ruta_p12, clave):
    """Devuelve (ok, texto). Abre el .p12 con la clave y lee titular y vigencia."""
    if not ruta_p12:
        return False, t("rev.sin_archivo")
    if not os.path.isfile(ruta_p12):
        return False, t("rev.no_existe")
    if not clave:
        return False, t("rev.sin_clave")
    try:
        firmante = cargar_firmante(ruta_p12, clave)
    except Exception:
        return False, t("rev.clave_mala")
    cert = firmante.signing_cert
    nombre = nombre_titular(cert)
    validez = cert["tbs_certificate"]["validity"]
    desde = validez["not_before"].native
    hasta = validez["not_after"].native
    ahora = datetime.datetime.now(datetime.timezone.utc)
    if hasta < ahora:
        return False, t("rev.vencida", nombre=nombre, fecha=f"{hasta:%d/%m/%Y}")
    if desde > ahora:
        return False, t("rev.futura", nombre=nombre, fecha=f"{desde:%d/%m/%Y}")
    dias = (hasta - ahora).days
    aviso = t("rev.vence_en", dias=dias) if dias <= 30 else ""
    return True, t("rev.valida", nombre=nombre, fecha=f"{hasta:%d/%m/%Y}", aviso=aviso)


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
                stamp_text=t("sello.texto_qr"),
                border_width=1,
                qr_position=QRPosition.LEFT_OF_TEXT,
            )
            parametros = {"url": texto_qr(firmante)}
        elif visible:
            estilo = TextStampStyle(
                stamp_text=t("sello.texto"),
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
