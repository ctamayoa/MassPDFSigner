# Cómo compilar

## Ejecutar sin compilar

Requiere Python 3.10 o superior.

```bash
pip install -e .
python -m firmador_masivo
```

## Compilar el programa en Windows

Desde la raíz del repositorio:

```powershell
pip install -e . pyinstaller
pyinstaller --noconfirm --windowed --name FirmadorPDF --paths src --collect-all pyhanko --collect-all pyhanko_certvalidator --collect-all aiohttp --collect-all qrcode --collect-binaries pymupdf --collect-data firmador_masivo --exclude-module onnxruntime --exclude-module numpy --exclude-module networkx --exclude-module pandas --exclude-module scipy --exclude-module matplotlib --exclude-module pymupdf.layout --exclude-module pymupdf4llm --exclude-module pymupdf_layout packaging/firmador_pdf.py
```

El resultado queda en la carpeta `dist\FirmadorPDF\` (ejecutable: `dist\FirmadorPDF\FirmadorPDF.exe`). También puedes usar `packaging\crear_exe.bat`.

Comprueba que funciona sin abrir ventanas:

```powershell
Start-Process dist\FirmadorPDF\FirmadorPDF.exe -ArgumentList "--autoprueba" -Wait -PassThru | Select-Object ExitCode
```

`ExitCode` debe ser `0`.

Notas:

- Se compila en **modo carpeta**, no en un solo `.exe`: abre más rápido y se comprime mucho mejor. Un `--onefile` con todas las librerías pesa más de 150 MB.
- `packaging/firmador_pdf.py` es un archivo mínimo que llama a `firmador_masivo.gui.main()`. Se usa en lugar de `python -m` porque PyInstaller necesita un script como punto de entrada.
- `--collect-all` incluye los archivos de datos de esa librería; sin ellos el programa falla al arrancar. `--collect-data firmador_masivo` incluye los textos de los idiomas.
- Se excluyen `numpy`, `onnxruntime` y las extensiones de diseño de PyMuPDF: se instalan como dependencias de PyMuPDF pero este programa no las usa, y juntas pesan más de 100 MB.
- Compila con la misma versión de Python con la que vas a distribuir (el flujo de GitHub usa 3.13).

## Crear el instalador

Requiere [Inno Setup 6](https://jrsoftware.org/isinfo.php). Con la carpeta `dist\FirmadorPDF\` ya generada:

```powershell
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" /DAppVersion=1.0.1 packaging\instalador.iss
```

Genera `dist\FirmadorPDF-Setup-1.0.1.exe`. Se instala sin permisos de administrador (por usuario), con acceso en el menú Inicio, desinstalador y asistente en español, inglés y portugués.

## Comprobar el resultado

Calcula el SHA256 para compararlo con el publicado en la Release:

```powershell
(Get-FileHash .\dist\FirmadorPDF-Setup-1.0.1.exe -Algorithm SHA256).Hash
```

Dos compilaciones del mismo código en máquinas distintas pueden dar hashes diferentes; la comparación es válida contra el archivo que descargas de la Release, no contra uno compilado por ti.

## Publicar una versión (mantenedores)

La compilación oficial la hace GitHub Actions al subir una etiqueta:

1. Cambia la versión en `src/firmador_masivo/_version.py` (único lugar).
2. En `CHANGELOG.md`, mueve lo de `[Unreleased]` a una sección nueva con la versión y la fecha.
3. Haz merge a `main` con el CI en verde.
4. Crea y sube la etiqueta:

   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

El flujo `.github/workflows/release.yml` comprueba que la etiqueta coincide con `_version.py`, corre las pruebas, compila el programa en Windows, lo comprueba con `--autoprueba`, crea el instalador y la versión portátil, calcula sus SHA256 y los publica en la Release, con las notas tomadas del `CHANGELOG`.

## Si el antivirus bloquea el `.exe`

Un programa de PyInstaller sin firma digital suele generar falsos positivos. Opciones: compilarlo tú mismo desde el código, o distribuir el programa como código fuente. Existen programas de firma de código gratuitos para proyectos de código abierto (por ejemplo, SignPath Foundation); este proyecto aún no los usa.
