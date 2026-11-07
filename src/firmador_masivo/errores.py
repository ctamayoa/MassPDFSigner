"""Traduce errores técnicos a mensajes claros en español.

El detalle técnico no se muestra al usuario: se deja en el registro de depuración
(logger "firmador_masivo")."""
import logging

log = logging.getLogger("firmador_masivo")

MSG_DANADO = "El archivo está dañado o no es un PDF válido."
MSG_CIFRADO = "El PDF está protegido con contraseña o cifrado."
MSG_ACCESO = "No se pudo leer o guardar el archivo. Revisa que no esté abierto en otro programa."
MSG_NO_EXISTE = "No se encontró el archivo."
MSG_GENERICO = "No se pudo firmar este archivo."

_PISTAS_DANADO = ("failed to open", "broken document", "cannot open", "not a pdf", "startxref",
                  "xref", "no /root", "trailer", "eof marker", "no objects found", "invalid pdf",
                  "unexpected end", "premature end", "header", "malformed")
_PISTAS_CIFRADO = ("encrypt", "password", "decrypt")


def describir_error(exc):
    """Devuelve un texto breve en español para mostrar al usuario."""
    log.debug("Error al procesar un PDF", exc_info=exc)
    nombre = type(exc).__name__
    texto = str(exc).lower()
    if isinstance(exc, FileNotFoundError):
        return MSG_NO_EXISTE
    if isinstance(exc, PermissionError):
        return MSG_ACCESO
    if any(p in texto for p in _PISTAS_CIFRADO):
        return MSG_CIFRADO
    if nombre in ("FileDataError", "PdfReadError", "PdfStreamError") or any(p in texto for p in _PISTAS_DANADO):
        return MSG_DANADO
    if isinstance(exc, OSError):
        return MSG_ACCESO
    return MSG_GENERICO
