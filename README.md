# Firmador Masivo PDF

Aplicación de escritorio para Windows que firma cientos o miles de PDFs de una sola vez con uno o dos certificados de firma electrónica (`.p12` / `.pfx`). No necesita consola: eliges tus firmas, la carpeta con los PDFs, dibujas con el mouse dónde va cada firma y pulsas **FIRMAR DOCUMENTOS**.

## Qué hace

- Firma con **dos certificados a la vez** (o con uno solo).
- **Firma visible** en la posición que dibujes sobre una vista previa, con **código QR** opcional.
- **Evita tapar el contenido**: detecta texto e imágenes bajo las firmas y las mueve a un lugar libre. Si no hay espacio, no firma ese PDF y lo deja anotado en el informe.
- **Subcarpetas**: puede recorrer todo un árbol y replica la misma estructura en la carpeta de salida. Nunca modifica los originales.
- **Reanudar**: omite lo que ya está firmado, así puedes continuar si se interrumpe. También puedes pausar, reanudar y detener.
- **Sello de tiempo** (TSA) opcional.
- **Validación previa** de los certificados (contraseña y vigencia) antes de empezar.
- **Informes** en cada corrida: `resumen_firmado_*.txt`, `registro_firmado_*.csv` (se abre en Excel) y `errores_firmado.txt`.

Rendimiento de referencia: unos 0,2 segundos por PDF sin sello de tiempo.

## Instalación (Windows)

1. Entra a la sección **Releases** de este repositorio y descarga `FirmadorPDF.exe` y `FirmadorPDF.exe.sha256`.
2. Comprueba que el archivo no se alteró. En PowerShell, desde la carpeta de la descarga:

   ```powershell
   (Get-FileHash .\FirmadorPDF.exe -Algorithm SHA256).Hash
   ```

   El resultado debe coincidir con el texto de `FirmadorPDF.exe.sha256`.
3. Ejecuta `FirmadorPDF.exe`. No requiere instalar Python.

> El `.exe` no está firmado digitalmente, así que Windows o tu antivirus pueden mostrar una advertencia. Si prefieres no confiar en el binario, puedes compilarlo tú mismo: ver [docs/compilar.md](docs/compilar.md).

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

## Contribuir y seguridad

- Cómo colaborar: [CONTRIBUTING.md](CONTRIBUTING.md).
- Cómo reportar una vulnerabilidad: [SECURITY.md](SECURITY.md).
- Historial de cambios: [CHANGELOG.md](CHANGELOG.md).

**Nunca subas a un issue o a un pull request tus archivos `.p12`/`.pfx`, contraseñas ni PDFs reales.**

## Licencia

[GNU AGPL-3.0](LICENSE). Se usa esta licencia porque el programa incluye [PyMuPDF](https://pymupdf.readthedocs.io/), que se distribuye bajo AGPL-3.0. En la práctica: puedes usar el programa libremente, y si distribuyes una versión modificada (o la ofreces como servicio en red) debes publicar su código fuente con la misma licencia.

## Aviso

El programa aplica firmas digitales con el certificado que tú le proporcionas; no emite certificados ni es una entidad de certificación. La validez legal de una firma depende del certificado usado y de la normativa aplicable. Esto no es asesoría legal.
