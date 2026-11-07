"""Imprime las notas de una versión: su sección del CHANGELOG y los SHA256 de los archivos.

Uso: python packaging/notas_version.py v1.0.1 dist/SHA256SUMS.txt
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
    sumas = Path(sys.argv[2]).read_text(encoding="ascii").strip() if len(sys.argv) > 2 else ""
    texto = (Path(__file__).resolve().parent.parent / "CHANGELOG.md").read_text(encoding="utf-8")
    cuerpo = seccion(texto, version) or "Sin notas en el CHANGELOG."
    print(cuerpo)
    print()
    print("### Descarga")
    print()
    print(f"- **`FirmadorPDF-Setup-{version}.exe`** (instalador, recomendado): se instala en tu usuario sin permisos de administrador, con acceso en el menú Inicio y desinstalador.")
    print(f"- **`FirmadorPDF-portable-{version}.zip`** (portátil): no se instala. Extrae TODA la carpeta y ejecuta `FirmadorPDF.exe`. Sirve para memoria USB, equipos prestados o de clientes, o equipos donde no puedes instalar. Para quitarlo, borra la carpeta.")
    print()
    print("### Verificación (SHA256)")
    print()
    print(f"```\n{sumas}\n```")
    print()
    print("En PowerShell: `(Get-FileHash .\\ARCHIVO -Algorithm SHA256).Hash`. "
          "Los archivos no están firmados digitalmente: Windows o tu antivirus pueden mostrar una advertencia.")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
