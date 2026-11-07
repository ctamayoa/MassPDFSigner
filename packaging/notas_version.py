"""Imprime las notas de una versión: su sección del CHANGELOG y el SHA256 del .exe.

Uso: python packaging/notas_version.py v1.0.0 <sha256>
"""
import re
import sys
from pathlib import Path


def seccion(changelog, version):
    patron = re.compile(rf"^## \[{re.escape(version)}\].*?$(.*?)(?=^## \[|^\[[^\]]+\]: |\Z)", re.M | re.S)
    m = patron.search(changelog)
    return m.group(1).strip() if m else ""


def main():
    version = sys.argv[1].lstrip("v")
    sha = sys.argv[2] if len(sys.argv) > 2 else ""
    texto = (Path(__file__).resolve().parent.parent / "CHANGELOG.md").read_text(encoding="utf-8")
    cuerpo = seccion(texto, version) or "Sin notas en el CHANGELOG."
    print(cuerpo)
    print()
    print("### Verificación")
    print()
    print("SHA256 de `FirmadorPDF.exe`:")
    print()
    print(f"```\n{sha}\n```")
    print()
    print("El `.exe` no está firmado digitalmente: Windows o tu antivirus pueden mostrar una advertencia.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
