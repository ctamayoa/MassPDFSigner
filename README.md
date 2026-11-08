# Firmador Masivo PDF

**Español** · [English](README.en.md)

> **English:** Windows desktop app that batch-signs hundreds or thousands of PDFs with 1 to 4 `.p12` certificates, with visible signatures, optional QR and timestamp. The interface is in Spanish, English and Brazilian Portuguese. **[Read the README in English](README.en.md)** · [Download](https://github.com/ctamayoa/MassPDFSigner/releases/latest)

Aplicación de escritorio para Windows que firma cientos o miles de PDFs de una sola vez con uno a cuatro certificados de firma electrónica (`.p12` / `.pfx`). No necesita consola: eliges tus firmas, la carpeta con los PDFs, dibujas con el mouse dónde va cada firma y pulsas **FIRMAR DOCUMENTOS**.

## Qué hace

- Firma con **hasta cuatro certificados a la vez** (o con uno solo), cada uno en su propio recuadro.
- **Firma visible** en la posición que dibujes sobre una vista previa, con **código QR** opcional.
- **Evita tapar el contenido**: detecta texto e imágenes bajo las firmas y las mueve a un lugar libre. Si no hay espacio, no firma ese PDF y lo deja anotado en el informe.
- **Subcarpetas**: puede recorrer todo un árbol y replica la misma estructura en la carpeta de salida. Nunca modifica los originales.
- **Reanudar**: omite lo que ya está firmado, así puedes continuar si se interrumpe. También puedes pausar, reanudar y detener.
- **Sello de tiempo** (TSA) opcional.
- **Tres idiomas**: español, inglés y portugués (Brasil). Se cambia desde la propia ventana.
- **Validación previa** de los certificados (contraseña y vigencia) antes de empezar.
- **Informes** en cada corrida: `resumen_firmado_*.txt`, `registro_firmado_*.csv` (se abre en Excel) y `errores_firmado.txt`.

Rendimiento de referencia: unos 0,2 segundos por PDF sin sello de tiempo.

## Instalación (Windows)

1. Entra a la sección **Releases** de este repositorio y descarga `FirmadorPDF-Setup-X.Y.Z.exe` (instalador) y `SHA256SUMS.txt`. Si prefieres no instalar, descarga el `.zip` portátil, descomprímelo y ejecuta `FirmadorPDF.exe`.
2. Comprueba que el archivo no se alteró. En PowerShell, desde la carpeta de la descarga:

   ```powershell
   (Get-FileHash .\FirmadorPDF-Setup-X.Y.Z.exe -Algorithm SHA256).Hash
   ```

   El resultado debe coincidir con la línea de ese archivo en `SHA256SUMS.txt`.
3. Ejecuta el instalador. No pide permisos de administrador y no requiere instalar Python.

> Los archivos no están firmados digitalmente, así que Windows o tu antivirus pueden mostrar una advertencia. Si prefieres no confiar en el binario, puedes compilarlo tú mismo: ver [docs/compilar.md](docs/compilar.md).

### ¿Instalador o portátil?

| | Instalador (`FirmadorPDF-Setup-X.Y.Z.exe`, ~40 MB) | Portátil (`FirmadorPDF-portable-X.Y.Z.zip`, ~58 MB) |
| --- | --- | --- |
| Para quién | Tu equipo de trabajo de siempre | Equipos donde no puedes o no quieres instalar |
| Qué hace | Instala en tu usuario (sin administrador), acceso en el menú Inicio, desinstalador | Nada: descomprimes la carpeta y ejecutas `FirmadorPDF.exe` |
| Actualizar | Ejecuta el instalador nuevo encima | Reemplaza la carpeta |
| Quitarlo | Desde «Aplicaciones instaladas» de Windows | Borra la carpeta |

El portátil sirve para llevarlo en una memoria USB, usarlo en un equipo prestado o de un cliente, o en un equipo con permisos restringidos. No deja nada instalado; solo guarda tu idioma en `%APPDATA%\FirmadorMasivoPDF`. Descomprime **toda** la carpeta antes de ejecutar (no abras el `.exe` desde dentro del `.zip`).

## Uso

La guía paso a paso está en [docs/guia-de-usuario.md](docs/guia-de-usuario.md). Sobre la validez de las firmas, el sello de tiempo y por qué un lector de PDF puede decir «validez desconocida», lee [docs/validez-legal.md](docs/validez-legal.md).

## Ejecutar desde el código

Requiere Python 3.10 o superior.

```bash
pip install -e .
python -m firmador_masivo
```

## Pruebas

```bash
pip install -e ".[dev]"
pytest
```

Los certificados y PDFs de prueba se generan al vuelo: el repositorio no contiene ningún certificado. Las pruebas de la ventana necesitan pantalla; en Linux se ejecutan con `xvfb-run -a pytest`.

Read this in English: [README.en.md](README.en.md).

## Contribuir y seguridad

- Cómo colaborar: [CONTRIBUTING.md](CONTRIBUTING.md).
- Cómo reportar una vulnerabilidad: [SECURITY.md](SECURITY.md).
- Historial de cambios: [CHANGELOG.md](CHANGELOG.md).

**Nunca subas a un issue o a un pull request tus archivos `.p12`/`.pfx`, contraseñas ni PDFs reales.**

## Licencia

[GNU AGPL-3.0](LICENSE). Se usa esta licencia porque el programa incluye [PyMuPDF](https://pymupdf.readthedocs.io/), que se distribuye bajo AGPL-3.0. En la práctica: puedes usar el programa libremente, y si distribuyes una versión modificada (o la ofreces como servicio en red) debes publicar su código fuente con la misma licencia.

## Aviso

El programa aplica firmas digitales con el certificado que tú le proporcionas; no emite certificados ni es una entidad de certificación. La validez legal de una firma depende del certificado usado y de la normativa aplicable. Esto no es asesoría legal.
