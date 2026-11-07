"""Idiomas de la interfaz. Los textos viven en idiomas/<código>.json.

El español es el idioma base: si a otro idioma le falta una clave, se usa el texto en español.
Para agregar un idioma: crea idiomas/<código>.json con las mismas claves y añade el código a IDIOMAS.
"""
import json
import os
import sys
from importlib import resources
from pathlib import Path

IDIOMAS = {"es": "Español", "en": "English", "pt": "Português"}
BASE = "es"

_cache = {}
_actual = BASE


def _cargar(cod):
    if cod not in _cache:
        texto = resources.files("firmador_masivo.idiomas").joinpath(f"{cod}.json").read_text(encoding="utf-8")
        _cache[cod] = json.loads(texto)
    return _cache[cod]


def claves(cod):
    return _cargar(cod)


def fijar_idioma(cod):
    global _actual
    _actual = cod if cod in IDIOMAS else BASE


def idioma_actual():
    return _actual


def t(clave, **datos):
    """Texto de la interfaz en el idioma actual. Con datos, sustituye los marcadores {nombre}."""
    texto = _cargar(_actual).get(clave)
    if texto is None:
        texto = _cargar(BASE)[clave]
    return texto.format(**datos) if datos else texto


def en_todos(clave):
    """Valor de una clave en todos los idiomas (sin repetidos)."""
    vistos = []
    for cod in IDIOMAS:
        v = _cargar(cod).get(clave)
        if v is not None and v not in vistos:
            vistos.append(v)
    return vistos


# ------------------------------------------------------ preferencia guardada
def _ruta_config():
    base = os.environ.get("FIRMADOR_CONFIG_DIR")
    if not base:
        base = os.environ.get("APPDATA") or str(Path.home() / ".config")
        base = str(Path(base) / "FirmadorMasivoPDF")
    return Path(base) / "config.json"


def guardar_preferencia(cod):
    try:
        ruta = _ruta_config()
        ruta.parent.mkdir(parents=True, exist_ok=True)
        ruta.write_text(json.dumps({"idioma": cod}), encoding="utf-8")
    except OSError:
        pass  # no poder recordar el idioma no es grave


def detectar_idioma():
    """Idioma de Windows (o de la variable LANG en otros sistemas); español si no se reconoce."""
    try:
        if sys.platform == "win32":
            import ctypes
            primario = ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0x3FF
            return {0x0A: "es", 0x09: "en", 0x16: "pt"}.get(primario, BASE)
        lang = (os.environ.get("LC_ALL") or os.environ.get("LANG") or "")[:2].lower()
        return lang if lang in IDIOMAS else BASE
    except Exception:
        return BASE


def iniciar():
    """Aplica el idioma guardado o, la primera vez, el del sistema."""
    cod = None
    try:
        cod = json.loads(_ruta_config().read_text(encoding="utf-8")).get("idioma")
    except (OSError, ValueError):
        pass
    fijar_idioma(cod if cod in IDIOMAS else detectar_idioma())
    return _actual
