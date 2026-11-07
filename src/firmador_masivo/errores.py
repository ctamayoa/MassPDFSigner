"""Traduce errores técnicos a mensajes claros en el idioma de la interfaz.

El detalle técnico no se muestra al usuario: se deja en el registro de depuración
(logger "firmador_masivo")."""
import logging

from .i18n import t

log = logging.getLogger("firmador_masivo")

_PISTAS_DANADO = ("failed to open", "broken document", "cannot open", "not a pdf", "startxref",
                  "xref", "no /root", "trailer", "eof marker", "no objects found", "invalid pdf",
                  "unexpected end", "premature end", "header", "malformed")
_PISTAS_CIFRADO = ("encrypt", "password", "decrypt")


def describir_error(exc):
    """Devuelve un texto breve, en el idioma actual, para mostrar al usuario."""
    log.debug("Error al procesar un PDF", exc_info=exc)
    nombre = type(exc).__name__
    texto = str(exc).lower()
    if isinstance(exc, FileNotFoundError):
        return t("error.no_existe")
    if isinstance(exc, PermissionError):
        return t("error.acceso")
    if any(p in texto for p in _PISTAS_CIFRADO):
        return t("error.cifrado")
    if nombre in ("FileDataError", "PdfReadError", "PdfStreamError") or any(p in texto for p in _PISTAS_DANADO):
        return t("error.danado")
    if isinstance(exc, OSError):
        return t("error.acceso")
    return t("error.generico")
