"""Rutas y listado de PDFs."""
import os

PREFIJO_LARGO = "\\\\?\\"
PREFIJO_UNC = "\\\\?\\UNC\\"


def ruta_larga(p):
    """En Windows, rutas de 240+ caracteres (comunes en OneDrive/SharePoint) necesitan el prefijo especial."""
    p = os.path.abspath(p)
    if os.name == "nt" and len(p) >= 240 and not p.startswith(PREFIJO_LARGO):
        if p.startswith("\\\\"):
            return PREFIJO_UNC + p[2:]
        return PREFIJO_LARGO + p
    return p


def _norm(p):
    p = os.path.abspath(p)
    if p.startswith(PREFIJO_UNC):
        p = "\\\\" + p[len(PREFIJO_UNC):]
    elif p.startswith(PREFIJO_LARGO):
        p = p[len(PREFIJO_LARGO):]
    return os.path.normcase(p)


def listar_pdfs(entrada, salida, recursivo):
    """Devuelve rutas relativas de los PDFs. Si es recursivo, recorre todas las
    subcarpetas y nunca entra a la carpeta de salida (por si está dentro de la de origen)."""
    base = ruta_larga(entrada)
    if not os.path.isdir(base):
        return []
    if not recursivo:
        return sorted(f for f in os.listdir(base)
                      if f.lower().endswith(".pdf") and os.path.isfile(os.path.join(base, f)))
    out = _norm(salida) if salida else None
    resultado = []
    for raiz, dirs, archivos in os.walk(base):
        dirs[:] = sorted(d for d in dirs if _norm(os.path.join(raiz, d)) != out)
        for f in sorted(archivos):
            if f.lower().endswith(".pdf"):
                resultado.append(os.path.relpath(os.path.join(raiz, f), base))
    return sorted(resultado, key=lambda r: (os.path.dirname(r).lower(), os.path.basename(r).lower()))
