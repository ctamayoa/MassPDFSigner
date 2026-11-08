"""Verificación de firmas de PDFs ya firmados (pyHanko).

Es una ayuda técnica: revisa integridad, cambios posteriores, firmante, fecha, vigencia del
certificado al firmar y, si se cargan certificados raíz, la cadena de confianza.
No consulta revocación en línea y no reemplaza la validación oficial de una entidad acreditada."""
import datetime
import os

from asn1crypto import pem, x509
from pyhanko.pdf_utils.reader import PdfFileReader
from pyhanko.sign.diff_analysis import ModificationLevel
from pyhanko.sign.validation import validate_pdf_signature
from pyhanko.sign.validation.status import SignatureCoverageLevel
from pyhanko_certvalidator import ValidationContext

from .archivos import ruta_larga
from .errores import describir_error, log
from .firmas import nombre_titular
from .i18n import t

EXTENSIONES_RAIZ = (".crt", ".cer", ".pem", ".der")
# Del peor al mejor: el veredicto de un documento es el de su peor firma
ORDEN_VEREDICTO = ("invalida", "revisar", "integra", "valida")
# Código del resultado -> clave de texto (el código va tal cual al CSV; la clave, a la pantalla)
CLAVES_VEREDICTO = {
    "valida": "ver.v_valida", "integra": "ver.v_integra", "revisar": "ver.v_revisar",
    "invalida": "ver.v_invalida", "sin_firmas": "ver.v_sin_firmas", "error": "ver.v_error",
}


def cargar_raices(carpeta):
    """Lee los certificados raíz de una carpeta. Devuelve (certificados, leidos, ilegibles)."""
    certs, ilegibles = [], 0
    if not carpeta or not os.path.isdir(carpeta):
        return certs, 0, 0
    for nombre in sorted(os.listdir(carpeta)):
        if not nombre.lower().endswith(EXTENSIONES_RAIZ):
            continue
        try:
            with open(os.path.join(carpeta, nombre), "rb") as f:
                datos = f.read()
            if pem.detect(datos):
                certs.extend(x509.Certificate.load(der) for _, _, der in pem.unarmor(datos, multiple=True))
            else:
                certs.append(x509.Certificate.load(datos))
        except Exception as e:
            ilegibles += 1
            log.debug("No se pudo leer el certificado raíz %s", nombre, exc_info=e)
    return certs, len(certs), ilegibles


def _vigente_en(cert, momento):
    if momento is None:
        return False
    validez = cert["tbs_certificate"]["validity"]
    return validez["not_before"].native <= momento <= validez["not_after"].native


def _cambios(estado):
    if estado.coverage == SignatureCoverageLevel.ENTIRE_FILE:
        return "ninguno"
    nivel = estado.modification_level
    if nivel is not None and nivel <= ModificationLevel.FORM_FILLING:
        return "permitidos"   # otra firma o formulario agregados después
    return "sospechosos"


def _veredicto(integra, cambios, vigente, confianza):
    if not integra:
        return "invalida"
    if cambios == "sospechosos" or not vigente:
        return "revisar"
    if confianza != "confiable":
        return "integra"
    return "valida"


def _revisar_firma(firma, contexto, hay_raices):
    estado = validate_pdf_signature(firma, contexto)
    cert = firma.signer_cert
    sello = getattr(getattr(estado, "timestamp_validity", None), "timestamp", None)
    fecha = estado.signer_reported_dt
    momento = sello or fecha or datetime.datetime.now(datetime.timezone.utc)
    integra = bool(estado.intact and estado.valid)
    cambios = _cambios(estado)
    vigente = _vigente_en(cert, momento)
    confianza = ("confiable" if estado.trusted else "no_confiable") if hay_raices else "sin_raices"
    return {
        "campo": firma.field_name,
        "firmante": nombre_titular(cert),
        "emisor": cert.issuer.native.get("common_name") or cert.issuer.human_friendly,
        "fecha": fecha,
        "sello": sello,
        "integridad": integra,
        "cambios": cambios,
        "vigente": vigente,
        "confianza": confianza,
        "veredicto": _veredicto(integra, cambios, vigente, confianza),
    }


def verificar_pdf(ruta, raices=None):
    """Revisa todas las firmas de un PDF. Devuelve {'firmas': [...], 'error': texto o None}.
    Si el archivo no se puede leer, 'error' trae un mensaje claro y 'firmas' queda vacía."""
    raices = raices or []
    try:
        contexto = ValidationContext(trust_roots=raices or None, allow_fetching=False)
        with open(ruta_larga(ruta), "rb") as f:
            lector = PdfFileReader(f, strict=False)
            firmas = [_revisar_firma(s, contexto, bool(raices)) for s in lector.embedded_signatures]
        return {"firmas": firmas, "error": None}
    except Exception as e:
        return {"firmas": [], "error": describir_error(e)}


def veredicto_de(resultado):
    """Veredicto global de un archivo: 'sin_firmas', 'error' o el de su peor firma."""
    if resultado["error"]:
        return "error"
    if not resultado["firmas"]:
        return "sin_firmas"
    return min((f["veredicto"] for f in resultado["firmas"]), key=ORDEN_VEREDICTO.index)


def detalle(f):
    """Explicación breve, en el idioma de la interfaz, de por qué una firma tiene su resultado."""
    if not f["integridad"]:
        return t("ver.det_alterado")
    partes = []
    if f["cambios"] == "sospechosos":
        partes.append(t("ver.det_cambios_mal"))
    elif f["cambios"] == "permitidos":
        partes.append(t("ver.det_cambios_ok"))
    if not f["vigente"]:
        partes.append(t("ver.det_vencido"))
    if f["confianza"] == "no_confiable":
        partes.append(t("ver.det_no_confiable"))
    elif f["confianza"] == "sin_raices":
        partes.append(t("ver.det_sin_raices"))
    if not partes:
        partes.append(t("ver.det_ok"))
    return " ".join(partes)


def _fmt(dt):
    return dt.astimezone().strftime("%Y-%m-%d %H:%M:%S") if dt else ""


def aplanar(resultados):
    """Una fila por firma (o una por archivo sin firmas o con error).
    'resultados' es una lista de (ruta_relativa, resultado de verificar_pdf)."""
    filas = []
    for rel, res in resultados:
        base = {"archivo": rel, "campo": "", "firmante": "", "emisor": "", "fecha": "", "sello": "",
                "integridad": "", "cambios": "", "vigente": "", "confianza": ""}
        if res["error"]:
            filas.append({**base, "veredicto": "error", "mensaje": res["error"]})
        elif not res["firmas"]:
            filas.append({**base, "veredicto": "sin_firmas", "mensaje": t("ver.det_sin_firmas")})
        else:
            for f in res["firmas"]:
                filas.append({**base, "campo": f["campo"], "firmante": f["firmante"], "emisor": f["emisor"],
                              "fecha": _fmt(f["fecha"]), "sello": _fmt(f["sello"]),
                              "integridad": f["integridad"], "cambios": f["cambios"],
                              "vigente": f["vigente"], "confianza": f["confianza"],
                              "veredicto": f["veredicto"], "mensaje": detalle(f)})
    return filas


COLUMNAS_CSV = ["archivo", "firma", "firmante", "emisor", "fecha_firma", "sello_tiempo", "integridad",
                "cambios_posteriores", "vigente_al_firmar", "confianza", "resultado", "mensaje"]


def guardar_csv(ruta, filas):
    """Informe de verificación (separador ';', utf-8-sig: abre bien en Excel).
    Encabezados y códigos de resultado no se traducen, para no romper planillas."""
    import csv
    with open(ruta, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(COLUMNAS_CSV)
        for r in filas:
            w.writerow([r["archivo"], r["campo"], r["firmante"], r["emisor"], r["fecha"], r["sello"],
                        r["integridad"], r["cambios"], r["vigente"], r["confianza"], r["veredicto"],
                        r["mensaje"]])
